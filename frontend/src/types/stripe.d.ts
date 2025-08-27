declare module '@stripe/react-stripe-js' {
  import React from 'react';
  import { Stripe } from '@stripe/stripe-js';

  export interface ElementsProps {
    stripe: Stripe | null;
    options?: any;
    children: React.ReactNode;
  }

  export const Elements: React.FC<ElementsProps>;

  export function useStripe(): Stripe | null;
  export function useElements(): any;

  export interface CardElementProps {
    options?: any;
    onChange?: (event: any) => void;
    onFocus?: (event: any) => void;
    onBlur?: (event: any) => void;
    onReady?: (event: any) => void;
    onEscape?: (event: any) => void;
  }

  export const CardElement: React.FC<CardElementProps>;
} 