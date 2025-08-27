import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  Divider,
  Alert,
  CircularProgress,
  Grid,
} from '@mui/material';
import {
  CreditCard as CreditCardIcon,
  AccountBalance as BankIcon,
  Payment as PaymentIcon,
} from '@mui/icons-material';

export interface PaymentMethod {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
}

export interface PaymentFormData {
  amount: number;
  currency: string;
  paymentMethod: string;
  cardNumber?: string;
  expiryDate?: string;
  cvv?: string;
  cardholderName?: string;
  bankAccount?: string;
  routingNumber?: string;
  cardToken?: string; // Stripe card token for secure payment processing
}

interface PaymentFormProps {
  amount: number;
  currency?: string;
  onPaymentSubmit: (data: PaymentFormData) => Promise<void>;
  onCancel?: () => void;
  loading?: boolean;
  error?: string;
  availableMethods?: PaymentMethod[];
}

const PaymentForm: React.FC<PaymentFormProps> = ({
  amount,
  currency = 'USD',
  onPaymentSubmit,
  onCancel,
  loading = false,
  error,
  availableMethods = [
    {
      id: 'credit_card',
      name: 'Credit Card',
      icon: <CreditCardIcon />,
      description: 'Pay with Visa, Mastercard, or American Express',
    },
    {
      id: 'bank_transfer',
      name: 'Bank Transfer',
      icon: <BankIcon />,
      description: 'Direct bank transfer',
    },
    {
      id: 'paypal',
      name: 'PayPal',
      icon: <PaymentIcon />,
      description: 'Pay with your PayPal account',
    },
  ],
}) => {
  const [formData, setFormData] = useState<PaymentFormData>({
    amount,
    currency,
    paymentMethod: 'credit_card',
  });

  const [formErrors, setFormErrors] = useState<Partial<PaymentFormData>>({});

  const handleInputChange = (field: keyof PaymentFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    
    // Clear error when user starts typing
    if (formErrors[field]) {
      setFormErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  const validateForm = (): boolean => {
    const errors: Partial<PaymentFormData> = {};

    if (formData.paymentMethod === 'credit_card') {
      if (!formData.cardNumber || formData.cardNumber.length < 13) {
        errors.cardNumber = 'Please enter a valid card number';
      }
      if (!formData.expiryDate || !/^\d{2}\/\d{2}$/.test(formData.expiryDate)) {
        errors.expiryDate = 'Please enter expiry date (MM/YY)';
      }
      if (!formData.cvv || formData.cvv.length < 3) {
        errors.cvv = 'Please enter a valid CVV';
      }
      if (!formData.cardholderName) {
        errors.cardholderName = 'Please enter cardholder name';
      }
    } else if (formData.paymentMethod === 'bank_transfer') {
      if (!formData.bankAccount) {
        errors.bankAccount = 'Please enter bank account number';
      }
      if (!formData.routingNumber) {
        errors.routingNumber = 'Please enter routing number';
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await onPaymentSubmit(formData);
    } catch (error) {
      console.error('Payment submission error:', error);
    }
  };

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const renderPaymentMethodFields = () => {
    switch (formData.paymentMethod) {
      case 'credit_card':
        return (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Card Number"
                value={formData.cardNumber || ''}
                onChange={(e) => handleInputChange('cardNumber', e.target.value)}
                error={!!formErrors.cardNumber}
                helperText={formErrors.cardNumber}
                placeholder="1234 5678 9012 3456"
                inputProps={{ maxLength: 19 }}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Expiry Date"
                value={formData.expiryDate || ''}
                onChange={(e) => handleInputChange('expiryDate', e.target.value)}
                error={!!formErrors.expiryDate}
                helperText={formErrors.expiryDate}
                placeholder="MM/YY"
                inputProps={{ maxLength: 5 }}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="CVV"
                value={formData.cvv || ''}
                onChange={(e) => handleInputChange('cvv', e.target.value)}
                error={!!formErrors.cvv}
                helperText={formErrors.cvv}
                placeholder="123"
                inputProps={{ maxLength: 4 }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Cardholder Name"
                value={formData.cardholderName || ''}
                onChange={(e) => handleInputChange('cardholderName', e.target.value)}
                error={!!formErrors.cardholderName}
                helperText={formErrors.cardholderName}
                placeholder="John Doe"
              />
            </Grid>
          </Grid>
        );

      case 'bank_transfer':
        return (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Bank Account Number"
                value={formData.bankAccount || ''}
                onChange={(e) => handleInputChange('bankAccount', e.target.value)}
                error={!!formErrors.bankAccount}
                helperText={formErrors.bankAccount}
                placeholder="1234567890"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Routing Number"
                value={formData.routingNumber || ''}
                onChange={(e) => handleInputChange('routingNumber', e.target.value)}
                error={!!formErrors.routingNumber}
                helperText={formErrors.routingNumber}
                placeholder="123456789"
              />
            </Grid>
          </Grid>
        );

      case 'paypal':
        return (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="body2" color="text.secondary">
              You will be redirected to PayPal to complete your payment.
            </Typography>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Payment Details
        </Typography>

        {/* Payment Summary */}
        <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="h5" color="primary" gutterBottom>
            {formatCurrency(amount, currency)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Total amount to be charged
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          {/* Payment Method Selection */}
          <FormControl component="fieldset" sx={{ mb: 3, width: '100%' }}>
            <FormLabel component="legend">Payment Method</FormLabel>
            <RadioGroup
              value={formData.paymentMethod}
              onChange={(e) => handleInputChange('paymentMethod', e.target.value)}
            >
              {availableMethods.map((method) => (
                <FormControlLabel
                  key={method.id}
                  value={method.id}
                  control={<Radio />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {method.icon}
                      <Box>
                        <Typography variant="body1">{method.name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {method.description}
                        </Typography>
                      </Box>
                    </Box>
                  }
                  sx={{ mb: 1 }}
                />
              ))}
            </RadioGroup>
          </FormControl>

          <Divider sx={{ my: 2 }} />

          {/* Payment Method Specific Fields */}
          {renderPaymentMethodFields()}

          {/* Action Buttons */}
          <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            {onCancel && (
              <Button
                variant="outlined"
                onClick={onCancel}
                disabled={loading}
              >
                Cancel
              </Button>
            )}
            <Button
              type="submit"
              variant="contained"
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : <PaymentIcon />}
            >
              {loading ? 'Processing...' : `Pay ${formatCurrency(amount, currency)}`}
            </Button>
          </Box>
        </form>
      </CardContent>
    </Card>
  );
};

export default PaymentForm; 