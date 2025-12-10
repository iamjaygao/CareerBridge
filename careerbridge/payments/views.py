from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import datetime, timedelta
import uuid
import stripe
from django.conf import settings

from .models import Payment, PaymentMethod, Refund, PaymentWebhook
from .serializers import (
    PaymentSerializer, PaymentCreateSerializer, PaymentMethodSerializer,
    PaymentMethodCreateSerializer, RefundSerializer, RefundCreateSerializer,
    PaymentIntentSerializer, PaymentConfirmationSerializer, PaymentStatisticsSerializer
)
from adminpanel.permissions import IsAdminUser, is_admin_level

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
                appointment = get_object_or_404(Appointment, id=serializer.validated_data['appointment_id'])
                payment_data['appointment'] = appointment
                payment_data['mentor'] = appointment.mentor
            elif serializer.validated_data.get('mentor_id'):
                from mentors.models import MentorProfile
                mentor = get_object_or_404(MentorProfile, id=serializer.validated_data['mentor_id'])
                payment_data['mentor'] = mentor
            
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
                    return Response({'error': 'Stripe not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                # Prepare Connect transfer data if mentor has a connected account
                transfer_data = None
                connect_enabled = True if not settings_obj else settings_obj.stripe_connect_enabled
                if connect_enabled and payment.mentor and getattr(payment.mentor, 'stripe_account_id', ''):
                    transfer_data = {
                        'destination': payment.mentor.stripe_account_id
                    }

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
                    idempotency_key=f"pi_{payment.id}_{uuid.uuid4()}",
                    application_fee_amount=int(payment.platform_fee * 100) if transfer_data else None,
                    transfer_data=transfer_data
                )

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
def confirm_payment(request):
    """Confirm payment completion"""
    serializer = PaymentConfirmationSerializer(data=request.data)
    if serializer.is_valid():
        payment_intent_id = serializer.validated_data['payment_intent_id']

        try:
            # Confirm via Stripe if Stripe provider
            stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
            payment = Payment.objects.filter(user=request.user, provider='stripe', provider_payment_id=payment_intent_id).first()
            if not payment:
                return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if intent['status'] in ['succeeded', 'requires_capture']:
                payment.status = 'completed'
                payment.paid_at = timezone.now()
                payment.save()
                return Response({'payment_id': payment.id, 'status': 'completed'})
            else:
                return Response({'payment_id': payment.id, 'status': intent['status']}, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
                return Response({'error': 'Stripe not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            refund_obj = stripe.Refund.create(
                payment_intent=payment.provider_payment_id,
                amount=int(payment.amount * 100),
                idempotency_key=f"rf_{payment.id}_{uuid.uuid4()}"
            )

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
        
        # Calculate pending payouts (sum of mentor_earnings for completed payments not yet paid out)
        # This is a simplified calculation - in production, track actual payout status
        pending_payouts = float(mentor_earnings)  # Simplified: all mentor earnings are pending until paid
        
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

    # Handle PaymentIntent succeeded
    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        payment = Payment.objects.filter(provider='stripe', provider_payment_id=intent['id']).first()
        if payment and payment.status != 'completed':
            payment.status = 'completed'
            payment.paid_at = timezone.now()
            payment.save()
    elif event['type'] == 'payment_intent.payment_failed':
        intent = event['data']['object']
        payment = Payment.objects.filter(provider='stripe', provider_payment_id=intent['id']).first()
        if payment:
            payment.status = 'failed'
            payment.save()
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
    elif event['type'] == 'account.updated':
        acct = event['data']['object']
        account_id = acct.get('id')
        from mentors.models import MentorProfile
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
