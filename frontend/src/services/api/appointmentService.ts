import apiClient from './client';
import { Appointment } from '../../types';

export interface AppointmentFilters {
  status?: string;
  date_from?: string;
  date_to?: string;
  mentor_id?: number;
  sort_by?: string;
  page?: number;
}

export interface FeedbackData {
  rating: number;
  comment: string;
}

const appointmentService = {
  async getAppointments(filters?: AppointmentFilters): Promise<Appointment[]> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          params.append(key, value.toString());
        }
      });
    }
    const response = await apiClient.get<Appointment[]>('/appointments/appointments/', { params });
    return response.data;
  },

  async getAppointmentById(id: number): Promise<Appointment> {
    const response = await apiClient.get<Appointment>(`/appointments/appointments/${id}/`);
    return response.data;
  },

  async createAppointment(data: {
    mentor_id: number;
    service_id: number;
    scheduled_date: string;
    scheduled_time: string;
    user_notes?: string;
  }): Promise<Appointment> {
    const response = await apiClient.post<Appointment>('/mentors/sessions/', data);
    return response.data;
  },

  async cancelAppointment(id: number): Promise<void> {
    await apiClient.post(`/appointments/appointments/${id}/cancel/`);
  },

  async rescheduleAppointment(
    id: number,
    data: { scheduled_start: string; scheduled_end: string }
  ): Promise<Appointment> {
    const response = await apiClient.post<Appointment>(`/appointments/appointments/${id}/reschedule/`, data);
    return response.data;
  },

  async submitFeedback(id: number, feedback: FeedbackData): Promise<Appointment> {
    const response = await apiClient.post<Appointment>(`/appointments/appointments/${id}/feedback/`, feedback);
    return response.data;
  },

  async getMentorAvailability(
    mentorId: number,
    date: string
  ): Promise<{ start: string; end: string }[]> {
    const response = await apiClient.get<{ slots: { start: string; end: string }[] }>(
      `/mentors/${mentorId}/availability/`,
      { params: { date } }
    );
    return response.data.slots;
  },

  async getAvailableSlots(mentorId: number): Promise<any[]> {
    try {
      // Mock implementation - in production, this would call the actual API
      const today = new Date();
      const slots = [];
      
      for (let i = 0; i < 7; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() + i);
        
        const daySlots = [
          { datetime: `${date.toISOString().split('T')[0]}T09:00:00`, time: '9:00 AM' },
          { datetime: `${date.toISOString().split('T')[0]}T10:00:00`, time: '10:00 AM' },
          { datetime: `${date.toISOString().split('T')[0]}T11:00:00`, time: '11:00 AM' },
          { datetime: `${date.toISOString().split('T')[0]}T14:00:00`, time: '2:00 PM' },
          { datetime: `${date.toISOString().split('T')[0]}T15:00:00`, time: '3:00 PM' },
          { datetime: `${date.toISOString().split('T')[0]}T16:00:00`, time: '4:00 PM' },
        ];
        
        slots.push(...daySlots);
      }
      
      return slots;
    } catch (error) {
      console.error('Error fetching available slots:', error);
      return [];
    }
  },
};

export default appointmentService;