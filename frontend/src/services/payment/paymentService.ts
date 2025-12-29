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
  payment_id?: number;
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
  private baseURL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8001/api/v1';

  // Create payment intent on the server
  async createPaymentIntent(params: {
    amount: number;
    currency?: string;
    appointmentId?: number;
    mentorId?: number;
    paymentType?: string;
    provider?: string;
    description?: string;
  }): Promise<PaymentIntent> {
    try {
      const {
        amount,
        currency = 'USD',
        appointmentId,
        mentorId,
        paymentType = 'appointment',
        provider = 'stripe',
        description,
      } = params;
      const response = await fetch(`${this.baseURL}/payments/create-intent/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          amount,
          currency,
          appointment_id: appointmentId,
          mentor_id: mentorId,
          payment_type: paymentType,
          provider,
          description,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create payment intent');
      }

      const data = await response.json();
      return {
        payment_id: data.payment_id,
        id: data.payment_intent_id || data.id,
        amount: data.amount,
        currency: data.currency,
        status: data.status || 'processing',
        client_secret: data.client_secret,
      };
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
      const paymentIntent = await this.createPaymentIntent({
        amount: paymentData.amount,
        currency: paymentData.currency,
      });

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

        const confirmResponse = await fetch(`${this.baseURL}/payments/confirm/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify({
            payment_intent_id: confirmedIntent.id,
          }),
        });

        if (!confirmResponse.ok) {
          const errorData = await confirmResponse.json();
          return {
            success: false,
            error: errorData.error || 'Failed to confirm payment',
          };
        }

        return {
          success: true,
          paymentIntentId: confirmedIntent.id,
        };
      } else {
        return {
          success: false,
          error: 'Card token required. Use Stripe Elements to generate a token.',
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
      return {
        success: false,
        error: 'PayPal is not supported yet.',
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
      return {
        success: false,
        error: 'Bank transfer is not supported yet.',
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
      const response = await fetch(`${this.baseURL}/payments/list/`, {
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
  async getPaymentStatus(paymentId: number): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/payments/detail/${paymentId}/`, {
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
  async refundPayment(paymentId: number): Promise<PaymentResult> {
    try {
      const response = await fetch(`${this.baseURL}/payments/refund/${paymentId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
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
