from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import datetime, timedelta

from .models import Payment, PaymentMethod, Refund, PaymentWebhook
from .serializers import (
    PaymentSerializer, PaymentCreateSerializer, PaymentMethodSerializer,
    PaymentMethodCreateSerializer, RefundSerializer, RefundCreateSerializer,
    PaymentIntentSerializer, PaymentConfirmationSerializer, PaymentStatisticsSerializer
)

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
            
            payment = Payment.objects.create(**payment_data)
            
            # For now, return mock payment intent data
            # In production, this would integrate with Stripe/PayPal
            return Response({
                'payment_id': payment.id,
                'client_secret': f'pi_mock_{payment.id}_secret',
                'amount': payment.amount,
                'currency': payment.currency,
            })
            
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
            # Extract payment ID from mock payment intent ID
            payment_id = payment_intent_id.split('_')[2]
            payment = get_object_or_404(Payment, id=payment_id, user=request.user)
            
            # Update payment status
            payment.status = 'completed'
            payment.paid_at = timezone.now()
            payment.save()
            
            return Response({
                'payment_id': payment.id,
                'status': 'completed',
                'message': 'Payment confirmed successfully'
            })
            
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
        # Create refund record
        refund = Refund.objects.create(
            payment=payment,
            amount=payment.amount,
            currency=payment.currency,
            reason='requested_by_customer',
            description='User requested refund'
        )
        
        # Update payment status
        payment.status = 'refunded'
        payment.refunded_at = timezone.now()
        payment.save()
        
        return Response({
            'refund_id': refund.id,
            'status': 'refunded',
            'message': 'Refund processed successfully'
        })
        
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
@permission_classes([permissions.IsAdminUser])
def payment_statistics(request):
    """Get payment statistics for admin"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Overall statistics
    total_payments = Payment.objects.count()
    total_amount = Payment.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    successful_payments = Payment.objects.filter(status='completed').count()
    failed_payments = Payment.objects.filter(status='failed').count()
    refunded_payments = Payment.objects.filter(status='refunded').count()
    
    # Time-based statistics
    payments_today = Payment.objects.filter(created_at__date=today).count()
    payments_this_week = Payment.objects.filter(created_at__date__gte=week_ago).count()
    payments_this_month = Payment.objects.filter(created_at__date__gte=month_ago).count()
    
    revenue_today = Payment.objects.filter(
        status='completed', created_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    revenue_this_week = Payment.objects.filter(
        status='completed', created_at__date__gte=week_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    revenue_this_month = Payment.objects.filter(
        status='completed', created_at__date__gte=month_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Success rate
    success_rate = 0
    if total_payments > 0:
        success_rate = (successful_payments / total_payments) * 100
    
    # Average payment amount
    avg_payment = 0
    if successful_payments > 0:
        avg_payment = total_amount / successful_payments
    
    # Platform fees and mentor earnings
    platform_fees = Payment.objects.filter(status='completed').aggregate(
        total=Sum('platform_fee')
    )['total'] or 0
    
    mentor_earnings = Payment.objects.filter(status='completed').aggregate(
        total=Sum('mentor_earnings')
    )['total'] or 0
    
    data = {
        'total_payments': total_payments,
        'total_amount': total_amount,
        'successful_payments': successful_payments,
        'failed_payments': failed_payments,
        'refunded_payments': refunded_payments,
        'success_rate': round(success_rate, 2),
        'avg_payment': round(avg_payment, 2),
        'platform_fees': platform_fees,
        'mentor_earnings': mentor_earnings,
        'payments_today': payments_today,
        'payments_this_week': payments_this_week,
        'payments_this_month': payments_this_month,
        'revenue_today': revenue_today,
        'revenue_this_week': revenue_this_week,
        'revenue_this_month': revenue_this_month,
    }
    
    serializer = PaymentStatisticsSerializer(data)
    return Response(serializer.data)

# Webhook Views
@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    # For now, just log the webhook
    # In production, this would verify the signature and process the event
    webhook = PaymentWebhook.objects.create(
        provider='stripe',
        event_type='payment_intent.succeeded',
        event_id=f'evt_{timezone.now().timestamp()}',
        status='processed',
        payload=request.body.decode(),
        headers=dict(request.headers),
        processed_at=timezone.now()
    )
    
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
