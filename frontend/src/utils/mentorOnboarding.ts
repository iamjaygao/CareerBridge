/**
 * Mentor Onboarding Utilities
 * 
 * Handles mentor profile status checks in a product-correct way.
 * Missing mentor profile is an ONBOARDING STATE, not an ERROR.
 */

export interface MentorProfileStatus {
  has_profile: boolean;
  mentor_profile_id: number | null;
  application_status: string | null;
  can_update_profile: boolean;
}

/**
 * Defines which pages require a mentor profile to function.
 * Pages not listed here can work without a profile.
 */
export const requiresMentorProfile = (route: string): boolean => {
  const requiresProfile = [
    '/mentor/availability',
    '/mentor/earnings',
    '/mentor/payouts',
    '/mentor/services', // Services require profile for creation
  ];

  return requiresProfile.some((path) => route.includes(path));
};

/**
 * Defines which pages require Stripe Connect to be set up.
 * These pages should NOT call payout/earnings APIs if Stripe is not connected.
 * 
 * Missing Stripe is an ONBOARDING STATE (warning), not an error.
 * 403 from /payments/payouts/summary/ is EXPECTED when Stripe is not connected.
 */
export const requiresStripeConnect = (route: string): boolean => {
  const requiresStripe = [
    '/mentor/earnings',
    '/mentor/payouts',
  ];

  return requiresStripe.some((path) => route.includes(path));
};

/**
 * Get user-friendly onboarding message based on profile status.
 * Returns null if profile exists (no message needed).
 */
export const getOnboardingMessage = (
  profileStatus: MentorProfileStatus | null,
  context: 'availability' | 'services' | 'earnings' | 'generic'
): string | null => {
  if (!profileStatus || profileStatus.has_profile) {
    return null; // Profile exists, no message needed
  }

  const messages = {
    availability: 'Please create your mentor profile before setting availability.',
    services: 'Please create your mentor profile before adding services.',
    earnings: 'Please create your mentor profile to view earnings.',
    generic: 'Please complete your mentor profile to continue.',
  };

  return messages[context] || messages.generic;
};

/**
 * Check if we should block UI interaction based on profile status.
 * Returns true if profile is required but missing.
 */
export const shouldBlockInteraction = (
  profileStatus: MentorProfileStatus | null,
  requireProfile: boolean
): boolean => {
  if (!requireProfile) {
    return false; // Page doesn't require profile
  }

  return !profileStatus || !profileStatus.has_profile;
};

