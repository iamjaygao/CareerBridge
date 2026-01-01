// services/api/sessionService.ts
import apiClient from './client';

export interface CreateSessionPayload {
  time_slot_id: number;
  service_id: number;
  title?: string;
  description?: string;
}

export interface LockSlotPayload {
  time_slot_id: number;
  service_id: number;
  title?: string;
  description?: string;
}

export interface ReleaseSlotPayload {
  appointment_id: number;
  action: 'release';
}

class SessionService {
  async createSession(data: CreateSessionPayload): Promise<any> {
    return apiClient.post('/appointments/appointments/', data);
  }

  async lockSlot(data: LockSlotPayload): Promise<any> {
    return apiClient.post('/appointments/lock-slot/', data);
  }

  async releaseSlot(data: ReleaseSlotPayload): Promise<any> {
    return apiClient.post('/appointments/lock-slot/', data);
  }

  async getAvailableSlots(
    mentorId: number,
    date: string,
    serviceId?: number
  ): Promise<any> {
    return apiClient.get(`/mentors/${mentorId}/availability/slots/`, {
      params: {
        date,
        service_id: serviceId,
      },
    });
  }
}

export const sessionService = new SessionService();
