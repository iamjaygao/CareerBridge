from rest_framework import serializers
from .models import Payment, PaymentMethod, Refund, PaymentWebhook

class PaymentSerializer(serializers.ModelSerializer):
    """Payment serializer for API responses"""
    
    user = serializers.StringRelatedField()
    mentor = serializers.StringRelatedField()
    appointment = serializers.StringRelatedField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'mentor', 'appointment', 'payment_type', 'payment_type_display',
            'amount', 'currency', 'status', 'status_display', 'provider', 'provider_display',
            'platform_fee', 'mentor_earnings', 'tax_amount', 'total_amount',
            'description', 'is_completed', 'is_refundable',
            'created_at', 'paid_at', 'refunded_at'
        ]
        read_only_fields = [
            'id', 'user', 'mentor', 'appointment', 'platform_fee', 'mentor_earnings',
            'status', 'provider_payment_id', 'is_completed', 'is_refundable',
            'created_at', 'paid_at', 'refunded_at'
        ]

class PaymentCreateSerializer(serializers.ModelSerializer):
    """Payment creation serializer"""
    
    class Meta:
        model = Payment
        fields = [
            'mentor', 'appointment', 'payment_type', 'amount', 'currency',
            'provider', 'description'
        ]
    
    def validate(self, data):
        """Validate payment data"""
        # Ensure either mentor or appointment is provided
        if not data.get('mentor') and not data.get('appointment'):
            raise serializers.ValidationError("Either mentor or appointment must be provided")
        
        # Validate amount
        if data.get('amount', 0) <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        
        return data
    
    def create(self, validated_data):
        """Create payment with user from request"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class PaymentMethodSerializer(serializers.ModelSerializer):
    """Payment method serializer"""
    
    user = serializers.StringRelatedField()
    method_type_display = serializers.CharField(source='get_method_type_display', read_only=True)
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'user', 'method_type', 'method_type_display', 'provider',
            'is_default', 'is_active', 'last_four', 'card_brand',
            'expiry_month', 'expiry_year', 'created_at'
        ]
        read_only_fields = [
            'id', 'user', 'provider_token', 'created_at'
        ]

class PaymentMethodCreateSerializer(serializers.ModelSerializer):
    """Payment method creation serializer"""
    
    class Meta:
        model = PaymentMethod
        fields = [
            'method_type', 'provider', 'provider_token', 'is_default',
            'last_four', 'card_brand', 'expiry_month', 'expiry_year'
        ]
    
    def validate(self, data):
        """Validate payment method data"""
        # Validate card information for card type
        if data.get('method_type') == 'card':
            if not data.get('last_four'):
                raise serializers.ValidationError("Last four digits required for card")
            if not data.get('card_brand'):
                raise serializers.ValidationError("Card brand required for card")
        
        return data
    
    def create(self, validated_data):
        """Create payment method with user from request"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class RefundSerializer(serializers.ModelSerializer):
    """Refund serializer"""
    
    payment = serializers.StringRelatedField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    
    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'amount', 'currency', 'status', 'status_display',
            'reason', 'reason_display', 'description', 'is_completed',
            'created_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'payment', 'status', 'provider_refund_id', 'is_completed',
            'created_at', 'processed_at'
        ]

class RefundCreateSerializer(serializers.ModelSerializer):
    """Refund creation serializer"""
    
    class Meta:
        model = Refund
        fields = ['payment', 'amount', 'reason', 'description']
    
    def validate(self, data):
        """Validate refund data"""
        payment = data.get('payment')
        amount = data.get('amount')
        
        # Check if payment exists and is refundable
        if not payment.is_refundable:
            raise serializers.ValidationError("Payment is not refundable")
        
        # Check if refund amount is valid
        if amount > payment.amount:
            raise serializers.ValidationError("Refund amount cannot exceed payment amount")
        
        # Check if user owns the payment
        if payment.user != self.context['request'].user:
            raise serializers.ValidationError("You can only refund your own payments")
        
        return data

class PaymentWebhookSerializer(serializers.ModelSerializer):
    """Payment webhook serializer"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PaymentWebhook
        fields = [
            'id', 'provider', 'event_type', 'event_id', 'status', 'status_display',
            'processing_time', 'error_message', 'received_at', 'processed_at'
        ]
        read_only_fields = fields

class PaymentIntentSerializer(serializers.Serializer):
    """Payment intent creation serializer"""
    
    appointment_id = serializers.IntegerField(required=False)
    mentor_id = serializers.IntegerField(required=False)
    payment_type = serializers.ChoiceField(choices=Payment.PAYMENT_TYPE_CHOICES, default='appointment')
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3, default='USD')
    provider = serializers.ChoiceField(choices=Payment.PAYMENT_PROVIDER_CHOICES, default='stripe')
    description = serializers.CharField(max_length=255, required=False)
    
    def validate(self, data):
        """Validate payment intent data"""
        # Ensure either appointment_id or mentor_id is provided
        if not data.get('appointment_id') and not data.get('mentor_id'):
            raise serializers.ValidationError("Either appointment_id or mentor_id must be provided")
        
        # Validate amount
        if data.get('amount', 0) <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        
        return data

class PaymentConfirmationSerializer(serializers.Serializer):
    """Payment confirmation serializer"""
    
    payment_intent_id = serializers.CharField(max_length=100)
    payment_method_id = serializers.CharField(max_length=100, required=False)
    
    def validate_payment_intent_id(self, value):
        """Validate payment intent ID"""
        # Add validation logic here
        return value

class PaymentStatisticsSerializer(serializers.Serializer):
    """Payment statistics serializer"""
    
    total_payments = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    successful_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    refunded_payments = serializers.IntegerField()
    platform_fees = serializers.DecimalField(max_digits=12, decimal_places=2)
    mentor_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_payment_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    success_rate = serializers.FloatField()
    
    # Time-based statistics
    payments_today = serializers.IntegerField()
    payments_this_week = serializers.IntegerField()
    payments_this_month = serializers.IntegerField()
    revenue_today = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_this_week = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_this_month = serializers.DecimalField(max_digits=12, decimal_places=2) 