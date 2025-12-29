// services/api/sessionService.ts
import apiClient from './client';

export interface CreateSessionPayload {
  mentor_id: number;
  service_id: number;
  scheduled_date: string;
  scheduled_time: string;
  user_notes?: string;
  duration_minutes?: number;
}

export interface LockSlotPayload {
  time_slot_id: number;
  service_id: number;
  title?: string;
  description?: string;
}

class SessionService {
  async createSession(data: CreateSessionPayload): Promise<any> {
    return apiClient.post('/appointments/sessions/', data);
  }

  async lockSlot(data: LockSlotPayload): Promise<any> {
    return apiClient.post('/appointments/lock-slot/', data);
  }

  async getAvailableSlots(
    mentorId: number,
    date: string,
    serviceId?: number
  ): Promise<any> {
    return apiClient.get('/appointments/available-slots/', {
      params: {
        mentor_id: mentorId,
        date,
        service_id: serviceId,
      },
    });
  }
}

export const sessionService = new SessionService();
