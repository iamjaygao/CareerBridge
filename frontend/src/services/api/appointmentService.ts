import apiClient from './client';

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
   * Create appointment
   */
  async createAppointment(data: {
    mentor: number;
    date: string;
    time: string;
    notes?: string;
  }): Promise<any> {
    try {
      const response = await apiClient.post('/appointments/appointments/', data);
      return response.data;
    } catch (error) {
      console.error('Failed to create appointment:', error);
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
      const response = await apiClient.post(`/appointments/appointments/${id}/cancel/`, { reason });
      return response.data;
    } catch (error) {
      console.error('Failed to cancel appointment:', error);
      throw error;
    }
  }

  /**
   * Get available time slots for a mentor
   */
  async getAvailableTimeSlots(mentorId: number, date: string): Promise<any> {
    try {
      const response = await apiClient.get(`/appointments/available-slots/`, {
        params: { mentor: mentorId, date },
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get available time slots:', error);
      throw error;
    }
  }
}

// Use AppointmentFilters from types/index.ts instead
export type { AppointmentFilters } from '../../types';

// Keep old interface for backward compatibility (deprecated)
export interface AppointmentFiltersOld {
  status?: string;
  dateFrom?: string;
  dateTo?: string;
  mentor?: number;
}

const appointmentService = new AppointmentService();
export default appointmentService;

