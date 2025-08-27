import { loadStripe, Stripe } from '@stripe/stripe-js';
import { PaymentFormData } from '../../components/payments/PaymentForm';

// Initialize Stripe
let stripe: Stripe | null = null;

const initializeStripe = async () => {
  if (!stripe) {
    // Replace with your actual Stripe publishable key
    const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || '');
    stripe = await stripePromise;
  }
  return stripe;
};

export interface PaymentIntent {
  id: string;
  amount: number;
  currency: string;
  status: string;
  client_secret: string;
}

export interface PaymentResult {
  success: boolean;
  paymentIntentId?: string;
  error?: string;
}

class PaymentService {
  private baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

  // Create payment intent on the server
  async createPaymentIntent(amount: number, currency: string = 'USD'): Promise<PaymentIntent> {
    try {
      const response = await fetch(`${this.baseURL}/payments/create-intent/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          amount,
          currency,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create payment intent');
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating payment intent:', error);
      throw error;
    }
  }

  // Process payment with Stripe
  async processPayment(paymentData: PaymentFormData): Promise<PaymentResult> {
    try {
      const stripe = await initializeStripe();
      if (!stripe) {
        throw new Error('Stripe failed to initialize');
      }

      // Create payment intent
      const paymentIntent = await this.createPaymentIntent(paymentData.amount, paymentData.currency);

      // Handle different payment methods
      let result;
      
      switch (paymentData.paymentMethod) {
        case 'credit_card':
          result = await this.processCreditCardPayment(stripe, paymentIntent, paymentData);
          break;
        case 'paypal':
          result = await this.processPayPalPayment(paymentIntent, paymentData);
          break;
        case 'bank_transfer':
          result = await this.processBankTransferPayment(paymentIntent, paymentData);
          break;
        default:
          throw new Error('Unsupported payment method');
      }

      return result;
    } catch (error) {
      console.error('Payment processing error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Payment failed',
      };
    }
  }

  private async processCreditCardPayment(
    stripe: Stripe,
    paymentIntent: PaymentIntent,
    paymentData: PaymentFormData
  ): Promise<PaymentResult> {
    try {
      // For security reasons, card information should be collected via Stripe Elements
      // or processed server-side. This is a simplified approach for development.
      
      if (paymentData.cardToken) {
        // Use card token if available (from Stripe Elements)
        const { error, paymentIntent: confirmedIntent } = await stripe.confirmCardPayment(
          paymentIntent.client_secret,
          {
            payment_method: {
              card: {
                token: paymentData.cardToken,
              },
              billing_details: {
                name: paymentData.cardholderName,
              },
            },
          }
        );

        if (error) {
          return {
            success: false,
            error: error.message,
          };
        }

        return {
          success: true,
          paymentIntentId: confirmedIntent.id,
        };
      } else {
        // For development/testing: Send card data to server for processing
        // In production, always use Stripe Elements
        const response = await fetch(`${this.baseURL}/payments/process-card/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify({
            payment_intent_id: paymentIntent.id,
            card_number: paymentData.cardNumber,
            exp_month: parseInt(paymentData.expiryDate!.split('/')[0]),
            exp_year: parseInt('20' + paymentData.expiryDate!.split('/')[1]),
            cvc: paymentData.cvv,
            cardholder_name: paymentData.cardholderName,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          return {
            success: false,
            error: errorData.error || 'Failed to process card payment',
          };
        }

        const result = await response.json();

        return {
          success: true,
          paymentIntentId: result.payment_intent_id,
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Credit card payment failed',
      };
    }
  }

  private async processPayPalPayment(
    paymentIntent: PaymentIntent,
    paymentData: PaymentFormData
  ): Promise<PaymentResult> {
    try {
      // Redirect to PayPal for payment
      const response = await fetch(`${this.baseURL}/payments/paypal/create/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          payment_intent_id: paymentIntent.id,
          amount: paymentData.amount,
          currency: paymentData.currency,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create PayPal payment');
      }

      const { approval_url } = await response.json();
      
      // Redirect to PayPal
      window.location.href = approval_url;

      return {
        success: true,
        paymentIntentId: paymentIntent.id,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'PayPal payment failed',
      };
    }
  }

  private async processBankTransferPayment(
    paymentIntent: PaymentIntent,
    paymentData: PaymentFormData
  ): Promise<PaymentResult> {
    try {
      const response = await fetch(`${this.baseURL}/payments/bank-transfer/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          payment_intent_id: paymentIntent.id,
          bank_account: paymentData.bankAccount,
          routing_number: paymentData.routingNumber,
          amount: paymentData.amount,
          currency: paymentData.currency,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process bank transfer');
      }

      const result = await response.json();

      return {
        success: true,
        paymentIntentId: result.payment_intent_id,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Bank transfer failed',
      };
    }
  }

  // Get payment history
  async getPaymentHistory(): Promise<any[]> {
    try {
      const response = await fetch(`${this.baseURL}/payments/history/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch payment history');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching payment history:', error);
      throw error;
    }
  }

  // Get payment status
  async getPaymentStatus(paymentIntentId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/payments/status/${paymentIntentId}/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch payment status');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching payment status:', error);
      throw error;
    }
  }

  // Refund payment
  async refundPayment(paymentIntentId: string, amount?: number): Promise<PaymentResult> {
    try {
      const response = await fetch(`${this.baseURL}/payments/refund/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          payment_intent_id: paymentIntentId,
          amount,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process refund');
      }

      const result = await response.json();

      return {
        success: true,
        paymentIntentId: result.refund_id,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Refund failed',
      };
    }
  }
}

export default new PaymentService(); 