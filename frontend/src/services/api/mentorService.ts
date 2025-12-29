import apiClient from './client';

class MentorService {
  /**
   * Get all mentors
   */
  async getMentors(params?: any): Promise<any> {
    try {
      const response = await apiClient.get('/mentors/', { params });
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
      const response = await apiClient.get(`/mentors/${id}/`);
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
      const response = await apiClient.get(`/mentors/${mentorId}/availability/`, {
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
      const response = await apiClient.get(`/mentors/${mentorId}/reviews/`);
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
      const response = await apiClient.get('/mentors/payments/');
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
      const response = await apiClient.post('/mentors/apply/', data);
      return response.data;
    } catch (error) {
      console.error('Failed to apply as mentor:', error);
      throw error;
    }
  }

  /**
   * Update mentor profile
   */
  async updateMentorProfile(mentorId: number, data: any): Promise<any> {
    try {
      const response = await apiClient.put('/mentors/profile/update/', data);
      return response.data;
    } catch (error) {
      console.error('Failed to update mentor profile:', error);
      throw error;
    }
  }

  /**
   * Get mentor's own profile (for authenticated mentors)
   */
  async getMyProfile(): Promise<any> {
    try {
      // Try to get via profile update endpoint (if it supports GET)
      // Otherwise, this might need a dedicated endpoint
      const response = await apiClient.get('/mentors/profile/update/');
      return response.data;
    } catch (error) {
      console.error('Failed to get mentor profile:', error);
      throw error;
    }
  }

  /**
   * Update mentor's own profile (for authenticated mentors)
   */
  async updateMyProfile(data: any): Promise<any> {
    try {
      const response = await apiClient.patch('/mentors/profile/update/', data);
      return response.data;
    } catch (error) {
      console.error('Failed to update mentor profile:', error);
      throw error;
    }
  }

  /**
   * Get Stripe Connect status for mentor payouts
   */
  async getStripeStatus(): Promise<any> {
    try {
      const response = await apiClient.get('/mentors/connect/status/');
      return response.data;
    } catch (error) {
      console.error('Failed to get Stripe status:', error);
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
      const response = await apiClient.post('/mentors/connect/create-account/');
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
      const response = await apiClient.post('/mentors/connect/account-link/', null, {
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
      const response = await apiClient.get(`/mentors/${mentorId}/services/`);
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
      const response = await apiClient.post(`/mentors/${mentorId}/services/`, data);
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
      const response = await apiClient.patch(`/mentors/services/${serviceId}/update/`, data);
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
