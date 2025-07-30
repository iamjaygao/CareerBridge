# CareerBridge Payment Integration Guide

## 💳 Payment System Overview

CareerBridge supports multiple payment methods and providers to handle mentor session payments, resume analysis fees, and platform subscriptions.

## 🏦 Supported Payment Providers

### Primary Providers
- **Stripe** (Recommended for international)
- **PayPal** (Wide global coverage)
- **Square** (US-focused)

### Regional Providers
- **Alipay** (China)
- **WeChat Pay** (China)
- **Razorpay** (India)
- **Mercado Pago** (Latin America)

## 🏗️ Architecture

### Payment Flow
1. **User initiates payment** (booking appointment, resume analysis)
2. **System creates payment intent** with provider
3. **User completes payment** on frontend
4. **Provider confirms payment** via webhook
5. **System updates payment status** and triggers business logic
6. **Funds are distributed** (platform fee + mentor earnings)

### Database Models
```python
# payments/models.py
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES)
    provider = models.CharField(max_length=20)
    provider_payment_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
```

## 🔧 Implementation Steps

### 1. Install Dependencies
```bash
pip install stripe
pip install paypalrestsdk
pip install python-decouple
```

### 2. Environment Configuration
```env
# .env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
PAYPAL_MODE=sandbox  # or live
```

### 3. Create Payment App
```bash
python manage.py startapp payments
```

### 4. Payment Models
```python
# payments/models.py
from django.db import models
from django.conf import settings

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_PROVIDER_CHOICES = (
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('square', 'Square'),
    )
    
    # Basic information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mentor = models.ForeignKey('mentors.MentorProfile', on_delete=models.CASCADE, null=True, blank=True)
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.CASCADE, null=True, blank=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    provider = models.CharField(max_length=20, choices=PAYMENT_PROVIDER_CHOICES)
    
    # Provider information
    provider_payment_id = models.CharField(max_length=100, blank=True)
    provider_refund_id = models.CharField(max_length=100, blank=True)
    
    # Fee breakdown
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mentor_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['mentor', 'status']),
            models.Index(fields=['provider', 'provider_payment_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency} - {self.status}"
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_refundable(self):
        return self.status == 'completed' and not self.provider_refund_id
```

### 5. Payment Services
```python
# payments/services.py
import stripe
import paypalrestsdk
from django.conf import settings
from django.utils import timezone
from .models import Payment

class StripePaymentService:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    def create_payment_intent(self, payment):
        """Create Stripe payment intent"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(payment.amount * 100),  # Convert to cents
                currency=payment.currency.lower(),
                metadata={
                    'payment_id': payment.id,
                    'user_id': payment.user.id,
                    'mentor_id': payment.mentor.id if payment.mentor else '',
                    'appointment_id': payment.appointment.id if payment.appointment else '',
                },
                description=payment.description,
            )
            
            payment.provider_payment_id = intent.id
            payment.metadata['client_secret'] = intent.client_secret
            payment.save()
            
            return intent
            
        except stripe.error.StripeError as e:
            payment.status = 'failed'
            payment.metadata['error'] = str(e)
            payment.save()
            raise e
    
    def confirm_payment(self, payment_intent_id):
        """Confirm payment from webhook"""
        try:
            payment = Payment.objects.get(provider_payment_id=payment_intent_id)
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status == 'succeeded':
                payment.status = 'completed'
                payment.paid_at = timezone.now()
                payment.save()
                
                # Trigger business logic
                self._process_completed_payment(payment)
                
            return payment
            
        except Payment.DoesNotExist:
            raise ValueError(f"Payment not found for intent: {payment_intent_id}")
    
    def process_refund(self, payment, amount=None):
        """Process refund"""
        try:
            refund_amount = amount or payment.amount
            
            refund = stripe.Refund.create(
                payment_intent=payment.provider_payment_id,
                amount=int(refund_amount * 100),
            )
            
            payment.status = 'refunded'
            payment.provider_refund_id = refund.id
            payment.refunded_at = timezone.now()
            payment.save()
            
            return refund
            
        except stripe.error.StripeError as e:
            raise e
    
    def _process_completed_payment(self, payment):
        """Process business logic after payment completion"""
        if payment.appointment:
            # Update appointment status
            payment.appointment.is_paid = True
            payment.appointment.save()
            
            # Create mentor payment record
            self._create_mentor_payment(payment)
            
            # Send notifications
            self._send_payment_notifications(payment)
    
    def _create_mentor_payment(self, payment):
        """Create mentor payment record"""
        from mentors.models import MentorPayment
        
        MentorPayment.objects.create(
            mentor=payment.mentor,
            session=payment.appointment,
            total_amount=payment.amount,
            platform_fee=payment.platform_fee,
            mentor_earnings=payment.mentor_earnings,
            tax_amount=payment.tax_amount,
            payment_status='pending',
            payment_method=payment.provider,
            transaction_id=payment.provider_payment_id,
        )
    
    def _send_payment_notifications(self, payment):
        """Send payment notifications"""
        from notifications.models import Notification
        
        # Notify user
        Notification.objects.create(
            user=payment.user,
            notification_type='payment_success',
            title='Payment Successful',
            message=f'Your payment of {payment.amount} {payment.currency} has been processed successfully.',
            related_appointment=payment.appointment,
        )
        
        # Notify mentor
        if payment.mentor:
            Notification.objects.create(
                user=payment.mentor.user,
                notification_type='payment_received',
                title='Payment Received',
                message=f'You have received a payment of {payment.mentor_earnings} {payment.currency} for your session.',
                related_appointment=payment.appointment,
            )

class PayPalPaymentService:
    def __init__(self):
        paypalrestsdk.configure({
            'mode': settings.PAYPAL_MODE,
            'client_id': settings.PAYPAL_CLIENT_ID,
            'client_secret': settings.PAYPAL_CLIENT_SECRET,
        })
    
    def create_payment(self, payment):
        """Create PayPal payment"""
        paypal_payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": f"{settings.SITE_URL}/payments/paypal/success/",
                "cancel_url": f"{settings.SITE_URL}/payments/paypal/cancel/"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": payment.description,
                        "sku": f"payment_{payment.id}",
                        "price": str(payment.amount),
                        "currency": payment.currency,
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(payment.amount),
                    "currency": payment.currency
                },
                "description": payment.description
            }]
        })
        
        if paypal_payment.create():
            payment.provider_payment_id = paypal_payment.id
            payment.metadata['approval_url'] = paypal_payment.links[1].href
            payment.save()
            return paypal_payment
        else:
            payment.status = 'failed'
            payment.metadata['error'] = paypal_payment.error
            payment.save()
            raise Exception(paypal_payment.error)
```

### 6. Payment Views
```python
# payments/views.py
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .services import StripePaymentService, PayPalPaymentService
from .models import Payment

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_payment_intent(request):
    """Create payment intent for appointment booking"""
    appointment_id = request.data.get('appointment_id')
    
    try:
        appointment = Appointment.objects.get(id=appointment_id, user=request.user)
        
        # Calculate payment amount
        amount = appointment.price
        platform_fee = amount * 0.15  # 15% platform fee
        mentor_earnings = amount - platform_fee
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            mentor=appointment.mentor,
            appointment=appointment,
            amount=amount,
            currency=appointment.currency,
            platform_fee=platform_fee,
            mentor_earnings=mentor_earnings,
            provider='stripe',
            description=f"Session with {appointment.mentor.user.get_full_name()}",
        )
        
        # Create payment intent
        stripe_service = StripePaymentService()
        intent = stripe_service.create_payment_intent(payment)
        
        return Response({
            'client_secret': intent.client_secret,
            'payment_id': payment.id,
        })
        
    except Appointment.DoesNotExist:
        return Response(
            {'error': 'Appointment not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)
    
    if event['type'] == 'payment_intent.succeeded':
        stripe_service = StripePaymentService()
        stripe_service.confirm_payment(event['data']['object']['id'])
    
    return HttpResponse(status=200)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def process_refund(request, payment_id):
    """Process payment refund"""
    try:
        payment = Payment.objects.get(id=payment_id, user=request.user)
        
        if not payment.is_refundable:
            return Response(
                {'error': 'Payment is not refundable'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        stripe_service = StripePaymentService()
        refund = stripe_service.process_refund(payment)
        
        return Response({
            'refund_id': refund.id,
            'status': 'refunded',
        })
        
    except Payment.DoesNotExist:
        return Response(
            {'error': 'Payment not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
```

### 7. Frontend Integration
```typescript
// frontend/src/services/payment.ts
import { loadStripe } from '@stripe/stripe-js';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY!);

export const createPaymentIntent = async (appointmentId: number) => {
  const response = await apiClient.post('/payments/create-intent/', {
    appointment_id: appointmentId,
  });
  return response.data;
};

export const confirmPayment = async (clientSecret: string) => {
  const stripe = await stripePromise;
  if (!stripe) throw new Error('Stripe failed to load');
  
  const result = await stripe.confirmCardPayment(clientSecret, {
    payment_method: {
      card: elements.getElement('card')!,
      billing_details: {
        name: user.name,
        email: user.email,
      },
    },
  });
  
  if (result.error) {
    throw new Error(result.error.message);
  }
  
  return result.paymentIntent;
};
```

## 🔐 Security Considerations

### PCI Compliance
- Never store credit card data
- Use tokenization for sensitive data
- Implement proper encryption
- Regular security audits

### Fraud Prevention
- Implement rate limiting
- Monitor suspicious transactions
- Use 3D Secure authentication
- Implement address verification

### Data Protection
- Encrypt sensitive data at rest
- Secure API communications
- Implement proper logging
- Regular backup procedures

## 📊 Analytics and Reporting

### Payment Analytics
- Transaction volume
- Success/failure rates
- Average transaction value
- Payment method distribution

### Revenue Tracking
- Platform fees
- Mentor earnings
- Refund rates
- Revenue by region

## 🧪 Testing

### Test Cards
```bash
# Stripe Test Cards
4242 4242 4242 4242  # Successful payment
4000 0000 0000 0002  # Declined payment
4000 0000 0000 9995  # Insufficient funds

# PayPal Test Accounts
# Use PayPal sandbox accounts for testing
```

### Test Scenarios
- Successful payment flow
- Failed payment handling
- Refund processing
- Webhook handling
- Error scenarios

## 🚀 Deployment

### Production Checklist
- [ ] Update API keys to production
- [ ] Configure webhook endpoints
- [ ] Set up monitoring and alerts
- [ ] Test payment flows
- [ ] Implement error handling
- [ ] Set up backup procedures

### Monitoring
- Payment success rates
- Webhook delivery
- Error rates
- Response times
- Revenue metrics

## 📚 Resources

### Documentation
- [Stripe Documentation](https://stripe.com/docs)
- [PayPal Developer Documentation](https://developer.paypal.com/)
- [Square Developer Documentation](https://developer.squareup.com/)

### Tools
- [Stripe CLI](https://stripe.com/docs/stripe-cli)
- [PayPal Sandbox](https://developer.paypal.com/developer/accounts/)
- [Webhook Testing](https://webhook.site/)

---

**Happy Payment Integration! 💳** 