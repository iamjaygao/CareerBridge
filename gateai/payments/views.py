from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
import uuid
import stripe
from django.conf import settings
from django.db import transaction


from .models import Payment, PaymentMethod, Refund, PaymentWebhook
from .serializers import (
    PaymentSerializer, PaymentCreateSerializer, PaymentMethodSerializer,
    PaymentMethodCreateSerializer, RefundSerializer, RefundCreateSerializer,
    PaymentIntentSerializer, PaymentConfirmationSerializer, PaymentStatisticsSerializer
)
from adminpanel.permissions import IsAdminUser, is_admin_level
from signal_delivery.services.dispatcher import notify
from signal_delivery.services.rules import NotificationType
from payments.services import get_payout_settings, refresh_payout_status

# Stripe error helpers
def _stripe_not_configured():
    return Response({'error': 'Stripe not configured', 'service': 'stripe'}, status=status.HTTP_502_BAD_GATEWAY)

def _stripe_error_response(error):
    return Response({'error': str(error), 'service': 'stripe'}, status=status.HTTP_502_BAD_GATEWAY)

# Payment Views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_payment_intent(request):
    """Create payment intent for appointment booking"""
    serializer = PaymentIntentSerializer(data=request.data)
    if serializer.is_valid():
        try:
            # Create payment record
            payment_data = {
                'user': request.user,
                'payment_type': serializer.validated_data['payment_type'],
                'amount': serializer.validated_data['amount'],
                'currency': serializer.validated_data['currency'],
                'provider': serializer.validated_data['provider'],
                'description': serializer.validated_data.get('description', ''),
            }
            
            # Add mentor or appointment if provided
            if serializer.validated_data.get('appointment_id'):
                from appointments.models import Appointment

                appointment = get_object_or_404(
                    Appointment,
                    id=serializer.validated_data['appointment_id'],
                    user=request.user,  
                )

                # If the appointment is expired, return an error
                # The status must be pending
                if appointment.status != 'pending':
                    return Response(
                        {'error': 'Appointment is no longer payable'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # If there is a related slot, it must still be within the lock period
                slot = appointment.time_slot
                if (
                    slot
                    and slot.reserved_until
                    and timezone.now() > slot.reserved_until
                ):
                # Defensive repair: mark appointment as expired
                    appointment.status = 'expired'
                    appointment.save(update_fields=['status'])

                    return Response(
                        {'error': 'Appointment has expired, please rebook'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                payment_data['appointment'] = appointment
                payment_data['mentor'] = appointment.mentor
            
            # Compute platform fee/mentor earnings using MentorService percentages when available
            from decimal import Decimal
            from payments.models import PaymentSettings
            platform_fee_pct = Decimal('15.00')
            settings_obj = PaymentSettings.objects.order_by('-updated_at').first()
            if settings_obj:
                platform_fee_pct = settings_obj.platform_fee_percentage
            # Service-specific override
            if payment_data.get('appointment') and getattr(payment_data['appointment'], 'service', None):
                service = payment_data['appointment'].service
                if not settings_obj or settings_obj.allow_service_override:
                    platform_fee_pct = getattr(service, 'platform_fee_percentage', platform_fee_pct)
            platform_fee = Decimal(str(payment_data['amount'])) * (platform_fee_pct / Decimal('100'))
            mentor_earnings = Decimal(str(payment_data['amount'])) - platform_fee
            payment_data['platform_fee'] = platform_fee
            payment_data['mentor_earnings'] = mentor_earnings

            payment = Payment.objects.create(**payment_data)

            # Stripe PaymentIntent creation
            if payment.provider == 'stripe':
                stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
                if not stripe.api_key:
                    return _stripe_not_configured()

                try:
                    intent = stripe.PaymentIntent.create(
                        amount=int(payment.amount * 100),
                        currency=payment.currency.lower(),
                        metadata={
                            'payment_id': str(payment.id),
                            'user_id': str(request.user.id),
                            'payment_type': payment.payment_type,
                        },
                        description=payment.description or 'CareerBridge payment',
                        automatic_payment_methods={'enabled': True},
                        idempotency_key=f"pi_{payment.id}_{uuid.uuid4()}"
                    )
                except stripe.error.StripeError as e:
                    return _stripe_error_response(e)

                payment.provider_payment_id = intent['id']
                payment.status = 'processing'
                payment.save()

                return Response({
                    'payment_id': payment.id,
                    'provider': payment.provider,
                    'payment_intent_id': intent['id'],
                    'client_secret': intent['client_secret'],
                    'amount': payment.amount,
                    'currency': payment.currency,
                })

            # Other providers placeholder
            return Response({'payment_id': payment.id, 'amount': payment.amount, 'currency': payment.currency})
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_checkout_session(request):
    """Create Stripe Checkout Session for appointment payment"""
    appointment_id = request.data.get('appointment_id')
    
    if not appointment_id:
        return Response(
            {'error': 'appointment_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from appointments.models import Appointment
        appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)

        if appointment.time_slot:
            slot = appointment.time_slot
            if not slot.reserved_until or timezone.now() > slot.reserved_until:
                appointment.status = 'expired'
                appointment.save(update_fields=['status'])
                return Response(
                    {'error': 'Appointment expired, please rebook'},
                    status=400
                )

        
        # Check if appointment is in pending status
        if appointment.status != 'pending':
            return Response(
                {'error': 'Appointment is not in pending status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create Payment record
        payment, created = Payment.objects.get_or_create(
            appointment=appointment,
            user=request.user,
            defaults={
                'payment_type': 'appointment',
                'amount': appointment.price,
                'currency': appointment.currency,
                'provider': 'stripe',
                'description': f"Payment for appointment: {appointment.title}",
                'mentor': appointment.mentor,
                'status': 'pending',
            }
        )
        
        # Calculate platform fee and mentor earnings
        from decimal import Decimal
        from payments.models import PaymentSettings
        platform_fee_pct = Decimal('15.00')
        settings_obj = PaymentSettings.objects.order_by('-updated_at').first()
        if settings_obj:
            platform_fee_pct = settings_obj.platform_fee_percentage
        
        platform_fee = Decimal(str(payment.amount)) * (platform_fee_pct / Decimal('100'))
        mentor_earnings = Decimal(str(payment.amount)) - platform_fee
        payment.platform_fee = platform_fee
        payment.mentor_earnings = mentor_earnings
        payment.save()
        
        # Initialize Stripe
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        if not stripe.api_key:
            return _stripe_not_configured()
        
        # Create Stripe Checkout Session
        success_url = 'http://localhost:3000/student/appointments?payment=success&session_id={CHECKOUT_SESSION_ID}'
        cancel_url = 'http://localhost:3000/student/appointments?payment=cancel'
        
        try:
            session = stripe.checkout.Session.create(
                mode='payment',
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': payment.currency.lower(),
                        'product_data': {
                            'name': appointment.title,
                            'description': appointment.description or f"Appointment with {appointment.mentor.user.get_full_name() or appointment.mentor.user.username}",
                        },
                        'unit_amount': int(payment.amount * 100),
                    },
                    'quantity': 1,
                }],
                metadata={
                    'payment_id': str(payment.id),
                    'appointment_id': str(appointment.id),
                    'user_id': str(request.user.id),
                },
                success_url=success_url,
                cancel_url=cancel_url,
            )
        except stripe.error.StripeError as e:
            return _stripe_error_response(e)
        
        # Store session ID in payment (payment_intent will be set when checkout completes)
        payment.provider_payment_id = session.id
        payment.metadata['checkout_session_id'] = session.id
        payment.status = 'processing'
        payment.save()
        
        return Response({
            'checkout_url': session.url,
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def confirm_payment(request):
    """Confirm payment completion"""
    serializer = PaymentConfirmationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    payment_intent_id = serializer.validated_data['payment_intent_id']

    try:
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        if not stripe.api_key:
            return _stripe_not_configured()

        payment = Payment.objects.select_for_update().filter(
            user=request.user,
            provider='stripe',
            provider_payment_id=payment_intent_id
        ).first()

        if not payment:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

        # ✅ Payment-level idempotency
        if payment.status == 'completed':
            return Response({'payment_id': payment.id, 'status': 'completed'})

        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.StripeError as e:
            return _stripe_error_response(e)
        if intent['status'] not in ['succeeded', 'requires_capture']:
            return Response(
                {'payment_id': payment.id, 'status': intent['status']},
                status=status.HTTP_202_ACCEPTED
            )

        with transaction.atomic():
            payment.status = 'completed'
            payment.paid_at = timezone.now()
            payment.save(update_fields=['status', 'paid_at'])

            appointment = payment.appointment
            if appointment and appointment.status == 'pending':
                appointment.status = 'confirmed'
                appointment.is_paid = True
                appointment.save(update_fields=['status', 'is_paid'])

            if appointment:
                appointment_details = appointment.get_notification_details()
                mentor_name = (
                    appointment.mentor.user.get_full_name()
                    or appointment.mentor.user.username
                )

                notify(
                    NotificationType.APPOINTMENT_PAYMENT_SUCCESS,
                    context={
                        'appointment_id': appointment.id,
                        'student': payment.user,
                    },
                    title='Payment successful',
                    message=f'Payment of ${payment.amount} for {appointment_details} with {mentor_name} was successful',
                    priority='normal',
                    related_appointment=appointment,
                    payload=appointment.get_notification_payload(),
                )
                # Mentor should not receive payment status notifications.

        return Response({'payment_id': payment.id, 'status': 'completed'})

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reconcile_payment(request):
    """
    Fallback reconcile endpoint for frontend success redirects.
    If payment is completed but appointment is still pending, confirm it.
    """
    session_id = request.data.get('session_id')
    payment_intent_id = request.data.get('payment_intent_id')

    if not session_id and not payment_intent_id:
        return Response(
            {'error': 'session_id or payment_intent_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)

        payment = None
        if session_id:
            payment = Payment.objects.filter(
                user=request.user,
                provider='stripe'
            ).filter(
                Q(provider_payment_id=session_id) | Q(metadata__checkout_session_id=session_id)
            ).first()

        if not payment and payment_intent_id:
            payment = Payment.objects.filter(
                user=request.user,
                provider='stripe',
                provider_payment_id=payment_intent_id
            ).first()

        # Last-resort lookup via Stripe metadata if payment not found
        if not payment and session_id and stripe.api_key:
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                metadata = session.get('metadata') or {}
                payment_id = metadata.get('payment_id')
                if payment_id:
                    payment = Payment.objects.filter(
                        id=payment_id,
                        user=request.user,
                        provider='stripe'
                    ).first()

                if not payment and session.get('payment_intent'):
                    payment = Payment.objects.filter(
                        user=request.user,
                        provider='stripe',
                        provider_payment_id=session.get('payment_intent')
                    ).first()
            except stripe.error.StripeError as e:
                return _stripe_error_response(e)

        if not payment:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(id=payment.id)

            # If payment not completed, try to verify with Stripe
            if payment.status != 'completed' and stripe.api_key:
                verified = False

                if session_id:
                    try:
                        session = stripe.checkout.Session.retrieve(session_id)
                        if session.get('payment_status') == 'paid':
                            verified = True
                            payment_intent = session.get('payment_intent')
                            if payment_intent and payment.provider_payment_id != payment_intent:
                                payment.provider_payment_id = payment_intent
                    except stripe.error.StripeError as e:
                        return _stripe_error_response(e)

                if not verified and payment_intent_id:
                    try:
                        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                        if intent.get('status') in ['succeeded', 'requires_capture']:
                            verified = True
                    except stripe.error.StripeError as e:
                        return _stripe_error_response(e)

                if verified:
                    payment.status = 'completed'
                    if not payment.paid_at:
                        payment.paid_at = timezone.now()
                    payment.save(update_fields=['status', 'paid_at', 'provider_payment_id'])

            # Reconcile appointment if payment is completed
            _reconcile_appointment_from_payment(payment)

            # Send payment success notifications if appointment is confirmed
            payment.refresh_from_db()
            if payment.appointment:
                payment.appointment.refresh_from_db()
                if payment.status == 'completed' and payment.appointment.status == 'confirmed' and payment.appointment.is_paid:
                    appointment_details = payment.appointment.get_notification_details()
                    mentor_name = payment.appointment.mentor.user.get_full_name() or payment.appointment.mentor.user.username
                    notify(
                        NotificationType.APPOINTMENT_PAYMENT_SUCCESS,
                        context={
                            'appointment_id': payment.appointment.id,
                            'student': payment.user,
                        },
                        title='Payment successful',
                        message=f'Payment of ${payment.amount} for {appointment_details} with {mentor_name} was successful',
                        priority='normal',
                        related_appointment=payment.appointment,
                        payload=payment.appointment.get_notification_payload(),
                    )

        appointment = payment.appointment
        return Response({
            'payment_id': payment.id,
            'payment_status': payment.status,
            'appointment_id': appointment.id if appointment else None,
            'appointment_status': appointment.status if appointment else None,
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PaymentListView(generics.ListAPIView):
    """List user's payments"""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).select_related('mentor', 'appointment')

class PaymentDetailView(generics.RetrieveAPIView):
    """Get payment details"""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.all()
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).select_related('mentor', 'appointment')


class MentorPayoutSummaryView(APIView):
    """Get payout summary for the authenticated mentor"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'mentor_profile'):
            return Response({'error': 'Mentor profile required'}, status=status.HTTP_403_FORBIDDEN)

        mentor = request.user.mentor_profile
        payments = Payment.objects.filter(mentor=mentor, status='completed')

        for payment in payments:
            refresh_payout_status(payment)

        pending_total = payments.filter(payout_status='pending').aggregate(
            total=Sum('mentor_earnings')
        )['total'] or 0
        ready_total = payments.filter(payout_status='ready').aggregate(
            total=Sum('mentor_earnings')
        )['total'] or 0
        paid_total = payments.filter(payout_status='paid').aggregate(
            total=Sum('mentor_earnings')
        )['total'] or 0
        failed_total = payments.filter(payout_status='failed').aggregate(
            total=Sum('mentor_earnings')
        )['total'] or 0

        next_payout = payments.filter(
            payout_status='pending',
            payout_available_at__isnull=False
        ).order_by('payout_available_at').values_list('payout_available_at', flat=True).first()

        payout_settings = get_payout_settings()

        return Response({
            'pending_total': float(pending_total),
            'ready_total': float(ready_total),
            'paid_total': float(paid_total),
            'failed_total': float(failed_total),
            'next_payout_at': next_payout.isoformat() if next_payout else None,
            'payout_hold_days': payout_settings.hold_days,
            'payout_requires_admin_approval': payout_settings.requires_admin_approval,
            'payouts_enabled': bool(getattr(mentor, 'payouts_enabled', False)),
        })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def process_refund(request, payment_id):
    """Process payment refund"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if not payment.is_refundable:
        return Response(
            {'error': 'Payment is not refundable'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        if payment.provider == 'stripe':
            stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
            if not stripe.api_key:
                return _stripe_not_configured()

            try:
                refund_obj = stripe.Refund.create(
                    payment_intent=payment.provider_payment_id,
                    amount=int(payment.amount * 100),
                    idempotency_key=f"rf_{payment.id}_{uuid.uuid4()}"
                )
            except stripe.error.StripeError as e:
                return _stripe_error_response(e)

            refund = Refund.objects.create(
                payment=payment,
                amount=payment.amount,
                currency=payment.currency,
                reason='requested_by_customer',
                description='User requested refund',
                provider_refund_id=refund_obj['id'],
                status='completed',
                processed_at=timezone.now()
            )

            payment.status = 'refunded'
            payment.refunded_at = timezone.now()
            payment.save()

            return Response({'refund_id': refund.id, 'status': 'refunded'})
        
        return Response({'error': 'Unsupported provider'}, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )

# Payment Method Views
class PaymentMethodListView(generics.ListCreateAPIView):
    """List and create payment methods"""
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user, is_active=True)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PaymentMethodCreateSerializer
        return PaymentMethodSerializer

class PaymentMethodDetailView(generics.RetrieveDestroyAPIView):
    """Get and delete payment method"""
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_payment_method(request, method_id):
    """Delete payment method"""
    payment_method = get_object_or_404(PaymentMethod, id=method_id, user=request.user)
    payment_method.delete()
    return Response({'message': 'Payment method deleted successfully'})

# Refund Views
class RefundListView(generics.ListCreateAPIView):
    """List and create refunds"""
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Refund.objects.filter(payment__user=self.request.user).select_related('payment')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RefundCreateSerializer
        return RefundSerializer

class RefundDetailView(generics.RetrieveAPIView):
    """Get refund details"""
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Refund.objects.filter(payment__user=self.request.user).select_related('payment')

# Statistics View
@api_view(['GET'])
@permission_classes([IsAdminUser])
def payment_statistics(request):
    """Get payment statistics for admin"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(">>> DEBUG: entering payment_statistics")
    
    # Check if Payment model has any data
    total_payment_count = Payment.objects.count()
    logger.info(f">>> DEBUG: Total payments in database: {total_payment_count}")
    
    if total_payment_count == 0:
        logger.warning(">>> DEBUG: No payments found in database - returning zeros")
        return Response({
            'total_payments': 0,
            'total_amount': 0.0,
            'successful_payments': 0,
            'failed_payments': 0,
            'refunded_payments': 0,
            'success_rate': 0.0,
            'avg_payment': 0.0,
            'average_payment_amount': 0.0,
            'platform_fees': 0.0,
            'mentor_earnings': 0.0,
            'payments_today': 0,
            'payments_this_week': 0,
            'payments_this_month': 0,
            'revenue_today': 0.0,
            'revenue_this_week': 0.0,
            'revenue_this_month': 0.0,
            'pending_payouts': 0.0,
            'debug_message': 'No payment data found in database'
        })
    
    try:
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        logger.info(f">>> DEBUG: Date range - today: {today}, week_ago: {week_ago}, month_ago: {month_ago}")
        
        # Overall statistics - handle empty datasets safely
        total_payments = Payment.objects.count()
        logger.info(f">>> DEBUG: total_payments count: {total_payments}")
        
        total_amount_result = Payment.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )
        # Convert Decimal to float explicitly
        total_amount_raw = total_amount_result['total']
        if total_amount_raw is None:
            total_amount = 0.0
        else:
            # Handle both Decimal and float types
            from decimal import Decimal
            if isinstance(total_amount_raw, Decimal):
                total_amount = float(total_amount_raw)
            else:
                total_amount = float(total_amount_raw)
        logger.info(f">>> DEBUG: total_amount (completed): {total_amount}, type: {type(total_amount)}")
        
        successful_payments = Payment.objects.filter(status='completed').count()
        failed_payments = Payment.objects.filter(status='failed').count()
        refunded_payments = Payment.objects.filter(status='refunded').count()
        
        logger.info(f">>> DEBUG: successful: {successful_payments}, failed: {failed_payments}, refunded: {refunded_payments}")
        
        # Time-based statistics
        payments_today = Payment.objects.filter(created_at__date=today).count()
        payments_this_week = Payment.objects.filter(created_at__date__gte=week_ago).count()
        payments_this_month = Payment.objects.filter(created_at__date__gte=month_ago).count()
        
        logger.info(f">>> DEBUG: payments_today: {payments_today}, this_week: {payments_this_week}, this_month: {payments_this_month}")
        
        revenue_today_result = Payment.objects.filter(
            status='completed', created_at__date=today
        ).aggregate(total=Sum('amount'))
        # Convert Decimal to float explicitly
        from decimal import Decimal
        revenue_today_raw = revenue_today_result['total']
        if revenue_today_raw is None:
            revenue_today = 0.0
        else:
            revenue_today = float(revenue_today_raw) if isinstance(revenue_today_raw, Decimal) else float(revenue_today_raw)
        logger.info(f">>> DEBUG: revenue_today: {revenue_today}")
        
        revenue_this_week_result = Payment.objects.filter(
            status='completed', created_at__date__gte=week_ago
        ).aggregate(total=Sum('amount'))
        revenue_this_week_raw = revenue_this_week_result['total']
        if revenue_this_week_raw is None:
            revenue_this_week = 0.0
        else:
            revenue_this_week = float(revenue_this_week_raw) if isinstance(revenue_this_week_raw, Decimal) else float(revenue_this_week_raw)
        
        revenue_this_month_result = Payment.objects.filter(
            status='completed', created_at__date__gte=month_ago
        ).aggregate(total=Sum('amount'))
        revenue_this_month_raw = revenue_this_month_result['total']
        if revenue_this_month_raw is None:
            revenue_this_month = 0.0
        else:
            revenue_this_month = float(revenue_this_month_raw) if isinstance(revenue_this_month_raw, Decimal) else float(revenue_this_month_raw)
        
        # Success rate
        success_rate = 0.0
        if total_payments > 0:
            success_rate = float((successful_payments / total_payments) * 100)
        
        # Average payment amount
        avg_payment = 0.0
        if successful_payments > 0:
            avg_payment = float(total_amount / successful_payments)
        
        # Platform fees and mentor earnings
        platform_fees_result = Payment.objects.filter(status='completed').aggregate(
            total=Sum('platform_fee')
        )
        # Convert Decimal to float explicitly
        from decimal import Decimal
        platform_fees_raw = platform_fees_result['total']
        if platform_fees_raw is None:
            platform_fees = 0.0
        else:
            platform_fees = float(platform_fees_raw) if isinstance(platform_fees_raw, Decimal) else float(platform_fees_raw)
        logger.info(f">>> DEBUG: platform_fees: {platform_fees}, type: {type(platform_fees)}")
        
        mentor_earnings_result = Payment.objects.filter(status='completed').aggregate(
            total=Sum('mentor_earnings')
        )
        mentor_earnings_raw = mentor_earnings_result['total']
        if mentor_earnings_raw is None:
            mentor_earnings = 0.0
        else:
            mentor_earnings = float(mentor_earnings_raw) if isinstance(mentor_earnings_raw, Decimal) else float(mentor_earnings_raw)
        logger.info(f">>> DEBUG: mentor_earnings: {mentor_earnings}, type: {type(mentor_earnings)}")
        
        # Calculate pending payouts (completed payments not yet paid out)
        pending_payouts_result = Payment.objects.filter(
            status='completed',
            payout_status__in=['pending', 'ready', 'on_hold']
        ).aggregate(total=Sum('mentor_earnings'))['total'] or Decimal('0')
        pending_payouts = float(pending_payouts_result)
        
        # Ensure all values are JSON-serializable (no Decimal, no None)
        data = {
            'total_payments': int(total_payments),
            'total_amount': float(total_amount),
            'successful_payments': int(successful_payments),
            'failed_payments': int(failed_payments),
            'refunded_payments': int(refunded_payments),
            'success_rate': round(float(success_rate), 2),
            'avg_payment': round(float(avg_payment), 2),
            'average_payment_amount': round(float(avg_payment), 2),  # Add this field for serializer
            'platform_fees': float(platform_fees),
            'mentor_earnings': float(mentor_earnings),
            'payments_today': int(payments_today),
            'payments_this_week': int(payments_this_week),
            'payments_this_month': int(payments_this_month),
            'revenue_today': float(revenue_today),
            'revenue_this_week': float(revenue_this_week),
            'revenue_this_month': float(revenue_this_month),
            'pending_payouts': float(pending_payouts),  # Add pending_payouts field
        }
        
        # Verify all values are JSON-serializable
        import json
        try:
            json.dumps(data)
            logger.info(f">>> DEBUG: payment_statistics data is JSON-serializable: {data}")
        except (TypeError, ValueError) as e:
            logger.error(f">>> DEBUG: payment_statistics data is NOT JSON-serializable: {e}")
            logger.error(f">>> DEBUG: Problematic data: {data}")
        
        serializer = PaymentStatisticsSerializer(data=data)
        if serializer.is_valid():
            logger.info(">>> DEBUG: serializer is valid, returning validated_data")
            return Response(serializer.validated_data)
        else:
            logger.error(f">>> DEBUG: FINANCIAL API SERIALIZER ERROR: {serializer.errors}")
            # Return data directly if serializer fails, but log the error
            logger.error(">>> DEBUG: Returning raw data due to serializer validation failure")
            return Response(data, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f">>> DEBUG: FINANCIAL API ERROR: {str(e)}", exc_info=True)
        import traceback
        logger.error(f">>> DEBUG: Traceback: {traceback.format_exc()}")
        # Return error with details for debugging
        return Response(
            {
                'error': 'Failed to retrieve payment statistics',
                'detail': str(e),
                'exception_type': type(e).__name__,
                'total_payments': 0,
                'total_amount': 0.0,
                'successful_payments': 0,
                'failed_payments': 0,
                'refunded_payments': 0,
                'success_rate': 0.0,
                'avg_payment': 0.0,
                'average_payment_amount': 0.0,
                'platform_fees': 0.0,
                'mentor_earnings': 0.0,
                'payments_today': 0,
                'payments_this_week': 0,
                'payments_this_month': 0,
                'revenue_today': 0.0,
                'revenue_this_week': 0.0,
                'revenue_this_month': 0.0,
                'pending_payouts': 0.0,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Reconciliation helper: derives appointment status from payment status
def _reconcile_appointment_from_payment(payment: Payment):
    """
    Reconcile appointment status from payment status.
    Payment is the source of truth.
    
    INTERNAL ONLY - idempotent, safe to call multiple times.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    payment_id = payment.id
    
    # If payment.status is NOT a paid/completed state → return immediately
    if payment.status != 'completed':
        return
    
    # Fetch payment.appointment
    if not payment.appointment:
        return
    
    appointment = payment.appointment
    appointment_id = appointment.id
    
    # If appointment.status is already 'confirmed' → return (idempotent)
    if appointment.status == 'confirmed' and appointment.is_paid:
        return
    
    # Otherwise: set appointment.status = 'confirmed' and appointment.is_paid = True
    appointment.status = 'confirmed'
    appointment.is_paid = True
    appointment.save(update_fields=['status', 'is_paid'])
    from appointments.models import Appointment
    slot = getattr(appointment, 'time_slot', None)
    if slot:
        slot.is_available = False
        slot.reserved_until = None
        slot.reserved_appointment = appointment
        booked_count = Appointment.objects.filter(
            time_slot=slot,
            status__in=['confirmed', 'completed']
        ).count()
        if slot.current_bookings != booked_count:
            slot.current_bookings = booked_count
        slot.save(update_fields=[
            'is_available',
            'reserved_until',
            'reserved_appointment',
            'current_bookings',
        ])

    appointment_details = appointment.get_notification_details()
    notify(
        NotificationType.APPOINTMENT_CONFIRMED,
        context={
            'appointment_id': appointment.id,
            'student': appointment.user,
            'mentor': appointment.mentor.user,
        },
        title='Appointment confirmed',
        message=(
            f'Appointment ({appointment_details}) between {appointment.user.get_full_name() or appointment.user.username} '
            f'and {appointment.mentor.user.get_full_name() or appointment.mentor.user.username} is confirmed.'
        ),
        priority='normal',
        related_appointment=appointment,
        payload=appointment.get_notification_payload(),
    )
    
    logger.info(f"Payment reconciliation: payment {payment_id}, appointment {appointment_id} reconciled to confirmed")

# Helper function to finalize paid appointment
def _finalize_paid_appointment(payment: Payment):
    """
    Finalize booking when payment is confirmed.
    STRICTLY idempotent and irreversible: safe to call multiple times.
    Atomically confirms appointment and finalizes slot.
    ONLY called from checkout.session.completed webhook (authoritative event).
    
    Uses ONLY payment.appointment as the source of truth.
    """
    import logging
    logger = logging.getLogger(__name__)
    from appointments.models import Appointment, TimeSlot

    payment_id = payment.id

    # MUST use ONLY payment.appointment to determine which Appointment to finalize
    if not payment.appointment:
        logger.warning(f"Payment finalization: payment {payment_id} has no appointment, cannot finalize")
        return

    appointment = payment.appointment
    appointment_id = appointment.id

    # MUST run inside transaction.atomic()
    with transaction.atomic():
        # MUST select_for_update() the Payment row
        payment = Payment.objects.select_for_update().get(id=payment_id)
        
        # Refresh appointment reference after locking payment
        appointment = payment.appointment
        if not appointment:
            logger.warning(f"Payment finalization: payment {payment_id} has no appointment after lock, cannot finalize")
            return

        # MUST be strictly idempotent
        # If payment.status == 'completed' AND appointment.status == 'confirmed':
        if payment.status == 'completed' and appointment.status == 'confirmed' and appointment.is_paid:
            logger.info(f"Payment finalization: payment {payment_id}, appointment {appointment_id} already completed and confirmed (idempotent skip)")
            return

        # MUST set payment.status = 'completed' (using 'completed' as Payment model uses this, not 'paid')
        if payment.status != 'completed':
            payment.status = 'completed'
            update_fields = ['status']
            
            # payment.paid_at = timezone.now() (only if not already set)
            if not payment.paid_at:
                payment.paid_at = timezone.now()
                update_fields.append('paid_at')
            
            payment.save(update_fields=update_fields)

        # Lock appointment row
        appointment = Appointment.objects.select_for_update().get(id=appointment_id)
        
        # MUST NOT downgrade or reassign any confirmed appointment
        if appointment.status == 'confirmed' and appointment.is_paid:
            logger.info(f"Payment finalization: appointment {appointment_id} already confirmed and paid (idempotent skip)")
            return

        # Check if appointment is expired or cancelled (do not confirm these)
        if appointment.status in ['expired', 'cancelled']:
            logger.warning(f"Payment finalization: appointment {appointment_id} is {appointment.status}, cannot confirm")
            return

        # MUST set appointment.status = 'confirmed' and appointment.is_paid = True
        appointment.status = 'confirmed'
        appointment.is_paid = True
        appointment.save(update_fields=['status', 'is_paid'])

        # MUST finalize the slot consistently
        slot = getattr(appointment, 'time_slot', None)
        if slot:
            # Lock slot row
            slot = TimeSlot.objects.select_for_update().get(id=slot.id)
            
            # Finalize slot: mark unavailable, clear lock
            slot.is_available = False
            slot.reserved_until = None
            booked_count = Appointment.objects.filter(
                time_slot=slot,
                status__in=['confirmed', 'completed']
            ).count()
            slot.current_bookings = booked_count
            slot.save(update_fields=['is_available', 'reserved_until', 'current_bookings'])
            
            logger.info(f"Payment finalization: payment {payment_id}, appointment {appointment_id} confirmed and slot finalized successfully")
        else:
            logger.info(f"Payment finalization: payment {payment_id}, appointment {appointment_id} confirmed (no slot)")


# Webhook Views
@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
    if not endpoint_secret:
        return HttpResponse(status=500)

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Early idempotency: drop if event already recorded
    if PaymentWebhook.objects.filter(event_id=event['id']).exists():
        return HttpResponse(status=200)

    PaymentWebhook.objects.create(
        provider='stripe',
        event_type=event['type'],
        event_id=event['id'],
        status='processed',
        payload=event,
        headers=dict(request.headers),
        processed_at=timezone.now()
    )

    # Handle Checkout Session completed (AUTHORITATIVE EVENT - only this handler can finalize)
    if event['type'] == 'checkout.session.completed':
        import logging
        logger = logging.getLogger(__name__)
        
        session = event['data']['object']

        payment_status = session.get('payment_status')
        checkout_session_id = session.get('id')
        payment_intent_id = session.get('payment_intent')

        metadata = session.get('metadata') or {}
        payment_id = metadata.get('payment_id')

        logger.info(f"Payment webhook: checkout.session.completed (AUTHORITATIVE) - payment_id={payment_id}, payment_status={payment_status}")

        # Resolve Payment using provider_payment_id or metadata
        payment = None
        if payment_id:
            payment = Payment.objects.filter(
                id=payment_id,
                provider='stripe'
            ).first()
            logger.info(f"Payment webhook: payment {payment_id} resolved from metadata")

        if not payment and checkout_session_id:
            payment = Payment.objects.filter(
                provider='stripe',
                provider_payment_id=checkout_session_id
            ).first()
            if payment:
                logger.info(f"Payment webhook: payment {payment.id} resolved from checkout_session_id")

        # Sync provider_payment_id to payment_intent_id if needed
        if payment and payment_intent_id and payment.provider_payment_id != payment_intent_id:
            payment.provider_payment_id = payment_intent_id
            payment.save(update_fields=['provider_payment_id'])

        # Only finalize if payment_status is 'paid' and payment exists
        if payment_status == 'paid' and payment:
            # Update payment status to completed
            if payment.status != 'completed':
                payment.status = 'completed'
                if not payment.paid_at:
                    payment.paid_at = timezone.now()
                payment.save(update_fields=['status', 'paid_at'])
                logger.info(f"Payment webhook: payment {payment.id} status updated to completed")
            
            # Reconcile appointment from payment (Payment is source of truth)
            _reconcile_appointment_from_payment(payment)
            
            # Check if appointment was confirmed and send notifications
            payment.refresh_from_db()
            if payment.appointment:
                payment.appointment.refresh_from_db()
                if payment.appointment.status == 'confirmed' and payment.appointment.is_paid:
                    appointment_id = payment.appointment.id
                    logger.info(f"Payment webhook: payment {payment.id}, appointment {appointment_id} confirmed successfully")
                    
                    # Send notifications only after successful reconciliation
                    appointment_details = payment.appointment.get_notification_details()
                    mentor_name = payment.appointment.mentor.user.get_full_name() or payment.appointment.mentor.user.username
                    notify(
                        NotificationType.APPOINTMENT_PAYMENT_SUCCESS,
                        context={
                            'appointment_id': payment.appointment.id,
                            'student': payment.user,
                        },
                        title='Payment successful',
                        message=f'Payment of ${payment.amount} for {appointment_details} with {mentor_name} was successful',
                        priority='normal',
                        related_appointment=payment.appointment,
                        payload=payment.appointment.get_notification_payload(),
                    )
                    # Mentor should not receive payment status notifications.

        return HttpResponse(status=200)
        
    # Handle PaymentIntent succeeded (NON-AUTHORITATIVE - do NOT modify Appointment state)
    if event['type'] == 'payment_intent.succeeded':
        import logging
        logger = logging.getLogger(__name__)
        
        intent = event['data']['object']
        payment_intent_id = intent['id']
        
        # Try to find payment by provider_payment_id
        payment = Payment.objects.filter(provider='stripe', provider_payment_id=payment_intent_id).first()
        
        if payment and payment.appointment:
            appointment_id = payment.appointment.id
            logger.info(f"Payment webhook: payment_intent.succeeded (non-authoritative) - payment_intent_id={payment_intent_id}, appointment_id={appointment_id}, payment_id={payment.id} - IGNORED (only checkout.session.completed can finalize)")
        else:
            logger.info(f"Payment webhook: payment_intent.succeeded (non-authoritative) - payment_intent_id={payment_intent_id} - IGNORED (only checkout.session.completed can finalize)")
        
        # DO NOT modify Appointment or TimeSlot state
        # Return immediately - finalization happens only via checkout.session.completed
        return HttpResponse(status=200)
    
    # Handle Charge succeeded (NON-AUTHORITATIVE - do NOT modify Appointment state)
    if event['type'] == 'charge.succeeded':
        import logging
        logger = logging.getLogger(__name__)
        
        charge = event['data']['object']
        charge_id = charge.get('id')
        payment_intent_id = charge.get('payment_intent')
        
        # Try to find payment by payment_intent_id from charge
        payment = None
        if payment_intent_id:
            payment = Payment.objects.filter(provider='stripe', provider_payment_id=payment_intent_id).first()
        
        if payment and payment.appointment:
            appointment_id = payment.appointment.id
            logger.info(f"Payment webhook: charge.succeeded (non-authoritative) - charge_id={charge_id}, payment_intent_id={payment_intent_id}, appointment_id={appointment_id}, payment_id={payment.id} - IGNORED (only checkout.session.completed can finalize)")
        else:
            logger.info(f"Payment webhook: charge.succeeded (non-authoritative) - charge_id={charge_id}, payment_intent_id={payment_intent_id} - IGNORED (only checkout.session.completed can finalize)")
        
        # DO NOT modify Appointment or TimeSlot state
        # Return immediately - finalization happens only via checkout.session.completed
        return HttpResponse(status=200)
    
    elif event['type'] == 'payment_intent.payment_failed':
        intent = event['data']['object']
        payment = Payment.objects.filter(provider='stripe', provider_payment_id=intent['id']).first()
        if payment:
            payment.status = 'failed'
            payment.save()
            
            if payment.appointment:
                appointment_details = payment.appointment.get_notification_details()
                notify(
                    NotificationType.APPOINTMENT_PAYMENT_FAILED,
                    context={
                        'appointment_id': payment.appointment.id,
                        'student': payment.user,
                    },
                    title='Payment failed',
                    message=f'Payment of ${payment.amount} for {appointment_details} failed. Please try again.',
                    priority='high',
                    related_appointment=payment.appointment,
                    payload=payment.appointment.get_notification_payload(),
                )
                from django.contrib.auth import get_user_model

                User = get_user_model()
                staff_users = User.objects.filter(role="staff")
                failed_recent = Payment.objects.filter(
                    user=payment.user,
                    status='failed',
                    created_at__gte=timezone.now() - timezone.timedelta(days=7),
                ).count()
                for staff_user in staff_users:
                    notify(
                        NotificationType.STAFF_PAYMENT_FAILED,
                        context={
                            'payment_id': payment.id,
                            'appointment_id': payment.appointment.id,
                            'staff': staff_user,
                        },
                        title='Payment failed - staff follow-up',
                        message=(
                            f'Payment of ${payment.amount} for {appointment_details} failed. '
                            f'User: {payment.user.get_full_name() or payment.user.username}.'
                        ),
                        priority='urgent',
                        related_appointment=payment.appointment,
                        payload={
                            **payment.appointment.get_notification_payload(),
                            'payment_id': payment.id,
                        },
                    )
                    if failed_recent >= 3:
                        notify(
                            NotificationType.STAFF_REPEAT_FAILURE,
                            context={
                                'user_id': payment.user.id,
                                'staff': staff_user,
                            },
                            title='Repeated payment failures',
                            message=(
                                f'User {payment.user.get_full_name() or payment.user.username} '
                                f'has {failed_recent} failed payments in the last 7 days.'
                            ),
                            priority='high',
                            payload={'user_id': payment.user.id},
                        )
    elif event['type'] in ['charge.refunded', 'refund.updated']:
        data_obj = event['data']['object']
        # Try to find by payment_intent on charge
        payment_intent_id = data_obj.get('payment_intent') if isinstance(data_obj, dict) else None
        if payment_intent_id:
            payment = Payment.objects.filter(provider='stripe', provider_payment_id=payment_intent_id).first()
            if payment and payment.status != 'refunded':
                payment.status = 'refunded'
                payment.refunded_at = timezone.now()
                payment.save()
                from django.contrib.auth import get_user_model

                User = get_user_model()
                admin_users = User.objects.filter(role="admin")
                refund_count = Payment.objects.filter(
                    user=payment.user,
                    status='refunded',
                    refunded_at__gte=timezone.now() - timezone.timedelta(days=30),
                ).count()
                if refund_count >= 3:
                    for admin_user in admin_users:
                        notify(
                            NotificationType.ADMIN_REFUND_ALERT,
                            context={
                                'user_id': payment.user.id,
                                'admin': admin_user,
                            },
                            title='Multiple refunds detected',
                            message=(
                                f'User {payment.user.get_full_name() or payment.user.username} '
                                f'has {refund_count} refunds in the last 30 days.'
                            ),
                            priority='high',
                            payload={'user_id': payment.user.id},
                        )
    elif event['type'] == 'account.updated':
        acct = event['data']['object']
        account_id = acct.get('id')
        from human_loop.models import MentorProfile
        mentor = MentorProfile.objects.filter(stripe_account_id=account_id).first()
        if mentor:
            mentor.payouts_enabled = bool(acct.get('payouts_enabled'))
            mentor.charges_enabled = bool(acct.get('charges_enabled'))
            mentor.kyc_disabled_reason = acct.get('requirements', {}).get('disabled_reason', '') if acct.get('requirements') else ''
            due_by = acct.get('requirements', {}).get('current_deadline') if acct.get('requirements') else None
            mentor.kyc_due_by = timezone.datetime.fromtimestamp(due_by, tz=timezone.utc) if due_by else None
            mentor.stripe_capabilities = acct.get('capabilities', {}) or {}
            mentor.save()

    return HttpResponse(status=200)

@csrf_exempt
def paypal_webhook(request):
    """Handle PayPal webhooks"""
    # For now, just log the webhook
    webhook = PaymentWebhook.objects.create(
        provider='paypal',
        event_type='payment.completed',
        event_id=f'evt_{timezone.now().timestamp()}',
        status='processed',
        payload=request.body.decode(),
        headers=dict(request.headers),
        processed_at=timezone.now()
    )
    
    return HttpResponse(status=200)
