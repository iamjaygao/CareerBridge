import React, { useMemo, useState } from 'react';
import { loadStripe, Stripe } from '@stripe/stripe-js';
import { Elements, useStripe, useElements, CardElement } from '@stripe/react-stripe-js';
import { Alert, CircularProgress } from '@mui/material';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8001/api/v1';

const CheckoutInner: React.FC = () => {
  const stripe = useStripe();
  const elements = useElements();
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [paymentIntentId, setPaymentIntentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const createIntent = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(`${API_BASE_URL}/payments/create-intent/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mentor_id: 1, payment_type: 'appointment', amount: 10.0, currency: 'USD', provider: 'stripe', description: 'Demo payment' })
      });
      if (!res.ok) throw new Error('Failed to create intent');
      const data = await res.json();
      setClientSecret(data.client_secret);
      setPaymentIntentId(data.payment_intent_id);
    } catch (e: any) {
      setError(e.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handlePay = async () => {
    if (!stripe || !elements || !clientSecret) return;
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const card = elements.getElement(CardElement);
      if (!card) throw new Error('Card element not found');
      const result = await stripe.confirmCardPayment(clientSecret, {
        payment_method: {
          card,
        },
      });
      if (result.error) {
        throw new Error(result.error.message || 'Payment failed');
      }
      if (result.paymentIntent) {
        setSuccess(`Payment ${result.paymentIntent.status}`);
      }
    } catch (e: any) {
      setError(e.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>Stripe Payment Demo</h2>
      <button onClick={createIntent} disabled={loading}>{loading ? 'Creating...' : 'Create Payment Intent'}</button>
      <div style={{ marginTop: 16, maxWidth: 420 }}>
        <CardElement options={{ hidePostalCode: true }} />
      </div>
      <button onClick={handlePay} disabled={loading || !clientSecret} style={{ marginTop: 12 }}>{loading ? 'Processing...' : 'Pay'}</button>
      {paymentIntentId && <div style={{ marginTop: 8 }}>payment_intent_id: {paymentIntentId}</div>}
      {clientSecret && <div style={{ marginTop: 8 }}>client_secret: {clientSecret}</div>}
      {error && <Alert severity="error" style={{ marginTop: 8 }}>{error}</Alert>}
      {success && <Alert severity="success" style={{ marginTop: 8 }}>{success}</Alert>}
      <p style={{ marginTop: 16 }}>Use Stripe test card 4242 4242 4242 4242 (any future expiry, any CVC) for sandbox.</p>
    </div>
  );
};

const PaymentDemoPage: React.FC = () => {
  const stripePromise = useMemo(() => {
    const publishableKey = (window as any).STRIPE_PUBLISHABLE_KEY || process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY;
    return loadStripe(publishableKey || '');
  }, []);

  return (
    <Elements stripe={stripePromise as any}>
      <CheckoutInner />
    </Elements>
  );
};

export default PaymentDemoPage;