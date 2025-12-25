import apiClient from './client';

/**
 * Payload for creating mentor session (NEW – marketplace / mentor detail)
 */
export interface CreateSessionPayload {
  mentor_id: number;
  service_id: number;
  scheduled_date: string;
  scheduled_time: string;
  user_notes?: string;
  duration_minutes?: number;
}

/**
 * Payload for legacy appointment creation (OLD – keep for backward compatibility)
 */
export interface CreateAppointmentPayload {
  mentor: number;
  date: string;
  time: string;
  notes?: string;
}

class AppointmentService {
  /**
   * Get all appointments
   */
  async getAppointments(params?: any): Promise<any> {
    try {
      const response = await apiClient.get('/appointments/appointments/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get appointments:', error);
      throw error;
    }
  }

  /**
   * Get appointment by ID
   */
  async getAppointmentById(id: number): Promise<any> {
    try {
      const response = await apiClient.get(`/appointments/appointments/${id}/`);
      return response.data;
    } catch (error) {
      console.error('Failed to get appointment:', error);
      throw error;
    }
  }

  /**
   * Create appointment (LEGACY – do not remove)
   * Used by older pages
   */
  async createAppointment(data: {
    mentor: number;
    date: string;
    time: string;
    notes?: string;
  }): Promise<any> {
    return apiClient.post('/appointments/appointments/', data);
  }

  /**
   * Create mentor session (NEW – mentor detail / marketplace)
   */
  async createSession(
    data: CreateSessionPayload
  ): Promise<any> {
    try {
      const response = await apiClient.post('/appointments/appointments/', data);
      return response.data;
    } catch (error) {
      console.error('Failed to create session:', error);
      throw error;
    }
  }

  /**
   * Update appointment
   */
  async updateAppointment(id: number, data: any): Promise<any> {
    try {
      const response = await apiClient.put(`/appointments/appointments/${id}/`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to update appointment:', error);
      throw error;
    }
  }

  /**
   * Cancel appointment
   */
  async cancelAppointment(id: number, reason?: string): Promise<any> {
    try {
      const response = await apiClient.post(
        `/appointments/appointments/${id}/cancel/`,
        { reason }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to cancel appointment:', error);
      throw error;
    }
  }

}

// Export filters type (unchanged)
export type { AppointmentFilters } from '../../types';

// Deprecated legacy interface (keep for safety)
export interface AppointmentFiltersOld {
  status?: string;
  dateFrom?: string;
  dateTo?: string;
  mentor?: number;
}

const appointmentService = new AppointmentService();
export default appointmentService;
