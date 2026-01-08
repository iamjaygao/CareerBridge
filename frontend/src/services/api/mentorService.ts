import apiClient from './client';
import { OS_API } from '../../os/apiPaths';

class MentorService {
  /**
   * Get all mentors
   */
  async getMentors(params?: any): Promise<any> {
    try {
      const response = await apiClient.get(OS_API.HUMAN_LOOP, { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get mentors:', error);
      throw error;
    }
  }

  /**
   * Get mentor by ID
   */
  async getMentorById(id: number): Promise<any> {
    try {
      const response = await apiClient.get(`${OS_API.HUMAN_LOOP}${id}/`);
      return response.data;
    } catch (error) {
      console.error('Failed to get mentor:', error);
      throw error;
    }
  }

  /**
   * Get mentor availability
   */
  async getMentorAvailability(mentorId: number, date?: string, serviceId?: number): Promise<any> {
    try {
      const params: any = { date };
      if (serviceId) {
        params.service_id = serviceId;
      }
      const response = await apiClient.get(`${OS_API.HUMAN_LOOP}${mentorId}/availability/`, {
        params,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get mentor availability:', error);
      throw error;
    }
  }

  /**
   * Get mentor reviews
   */
  async getMentorReviews(mentorId: number): Promise<any> {
    try {
      const response = await apiClient.get(`${OS_API.HUMAN_LOOP}${mentorId}/reviews/`);
      return response.data;
    } catch (error) {
      console.error('Failed to get mentor reviews:', error);
      throw error;
    }
  }

  /**
   * Get mentor payments
   */
  async getMentorPayments(): Promise<any> {
    try {
      const response = await apiClient.get(`${OS_API.HUMAN_LOOP}payments/`);
      return response.data;
    } catch (error) {
      console.error('Failed to get mentor payments:', error);
      throw error;
    }
  }

  /**
   * Apply to become a mentor
   */
  async applyAsMentor(data: {
    expertise: string[];
    bio: string;
    price_per_hour: number;
    availability?: any;
  }): Promise<any> {
    try {
      const response = await apiClient.post(`${OS_API.HUMAN_LOOP}apply/`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to apply as mentor:', error);
      throw error;
    }
  }

  /**
   * Update mentor profile (WRITE operation)
   * 
   * GateAI OS Contract:
   * - This endpoint is WRITE-ONLY (PUT/PATCH)
   * - NEVER use GET on /profile/update/
   * - Requires explicit user action (form submit, button click)
   */
  async updateMentorProfile(mentorId: number, data: any): Promise<any> {
    try {
      const response = await apiClient.put(`${OS_API.HUMAN_LOOP}profile/update/`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to update mentor profile:', error);
      throw error;
    }
  }

  /**
   * Get mentor's own profile status (for authenticated mentors)
   * 
   * IMPORTANT: This uses the READ-ONLY profile status endpoint.
   * 
   * GateAI OS Contract:
   * - NEVER use /profile/update/ for GET requests (write-only endpoint)
   * - /profile/status/ is READ-ONLY and safe for auto-probing
   * - Returns: { has_profile, mentor_profile_id, application_status, can_update_profile }
   */
  async getMyProfile(): Promise<any> {
    try {
      // Use READ-ONLY profile status endpoint
      // This is safe for automatic probing/prefetching
      const response = await apiClient.get(`${OS_API.HUMAN_LOOP}profile/status/`);
      return response.data;
    } catch (error) {
      console.error('Failed to get mentor profile:', error);
      throw error;
    }
  }

  /**
   * Create mentor's own profile (for authenticated mentors)
   * 
   * GateAI OS Contract:
   * - This endpoint is WRITE-ONLY (POST)
   * - Use this when has_profile === false
   * - Requires explicit user action (form submit, button click)
   * - Returns 201 on success, 400 if profile already exists
   */
  async createMyProfile(data: any): Promise<any> {
    try {
      const response = await apiClient.post(`${OS_API.HUMAN_LOOP}profile/`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to create mentor profile:', error);
      throw error;
    }
  }

  /**
   * Update mentor's own profile (for authenticated mentors)
   * 
   * GateAI OS Contract:
   * - This endpoint is WRITE-ONLY (PATCH)
   * - Use this when has_profile === true
   * - NEVER use GET on /profile/update/
   * - Requires explicit user action (form submit, button click)
   */
  async updateMyProfile(data: any): Promise<any> {
    try {
      const response = await apiClient.patch(`${OS_API.HUMAN_LOOP}profile/update/`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to update mentor profile:', error);
      throw error;
    }
  }

  /**
   * Get Stripe Connect status for mentor payouts (READ-ONLY)
   * 
   * GateAI OS Contract:
   * - READ-ONLY endpoint, safe for auto-probing
   * - Returns: { is_connected, requires_action, can_set_availability, ... }
   */
  async getConnectStatus(): Promise<any> {
    try {
      const response = await apiClient.get(`${OS_API.HUMAN_LOOP}connect/status/`);
      return response.data;
    } catch (error) {
      console.error('Failed to get connect status:', error);
      throw error;
    }
  }

  /**
   * Legacy alias for getConnectStatus
   * @deprecated Use getConnectStatus() instead
   */
  async getStripeStatus(): Promise<any> {
    return this.getConnectStatus();
  }

  /**
   * Get payout status for current user (READ-ONLY)
   * 
   * GateAI OS Contract:
   * - READ-ONLY endpoint, safe for auto-probing
   * - Returns: { payout_enabled, requires_setup, has_stripe_account }
   */
  async getPayoutStatus(): Promise<any> {
    try {
      const response = await apiClient.get('/api/v1/payments/payouts/status/');
      return response.data;
    } catch (error) {
      console.error('Failed to get payout status:', error);
      throw error;
    }
  }

  /**
   * Get mentor payout summary
   */
  async getPayoutSummary(): Promise<any> {
    try {
      const response = await apiClient.get('/payments/payouts/summary/');
      return response.data;
    } catch (error) {
      console.error('Failed to get payout summary:', error);
      throw error;
    }
  }

  /**
   * Create Stripe Connect account
   */
  async createStripeAccount(): Promise<any> {
    try {
      const response = await apiClient.post(`${OS_API.HUMAN_LOOP}connect/create-account/`);
      return response.data;
    } catch (error) {
      console.error('Failed to create Stripe account:', error);
      throw error;
    }
  }

  /**
   * Create Stripe Connect account link
   */
  async createStripeAccountLink(returnUrl: string, refreshUrl: string): Promise<any> {
    try {
      const response = await apiClient.post(`${OS_API.HUMAN_LOOP}connect/account-link/`, null, {
        params: {
          return_url: returnUrl,
          refresh_url: refreshUrl,
        },
      });
      return response.data;
    } catch (error) {
      console.error('Failed to create Stripe account link:', error);
      throw error;
    }
  }

  /**
   * Get mentor's own services
   */
  async getMyServices(mentorId: number): Promise<any> {
    try {
      const response = await apiClient.get(`${OS_API.HUMAN_LOOP}${mentorId}/services/`);
      return response.data;
    } catch (error) {
      console.error('Failed to get mentor services:', error);
      throw error;
    }
  }

  /**
   * Create a mentor service
   */
  async createMentorService(mentorId: number, data: any): Promise<any> {
    try {
      const response = await apiClient.post(`${OS_API.HUMAN_LOOP}${mentorId}/services/`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to create mentor service:', error);
      throw error;
    }
  }

  /**
   * Update a mentor service
   */
  async updateMentorService(serviceId: number, data: any): Promise<any> {
    try {
      const response = await apiClient.patch(`${OS_API.HUMAN_LOOP}services/${serviceId}/update/`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to update mentor service:', error);
      throw error;
    }
  }
}

// Use MentorFilters from types/index.ts instead
export type { MentorFilters } from '../../types';

const mentorService = new MentorService();
export default mentorService;
