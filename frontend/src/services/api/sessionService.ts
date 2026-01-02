// services/api/sessionService.ts
import apiClient from './client';
import { OS_API } from '../../os/apiPaths';

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
    return apiClient.post(`${OS_API.DECISION_SLOTS}appointments/`, data);
  }

  async lockSlot(data: LockSlotPayload): Promise<any> {
    return apiClient.post(`${OS_API.DECISION_SLOTS}lock-slot/`, data);
  }

  async releaseSlot(data: ReleaseSlotPayload): Promise<any> {
    return apiClient.post(`${OS_API.DECISION_SLOTS}lock-slot/`, data);
  }

  async getAvailableSlots(
    mentorId: number,
    date: string,
    serviceId?: number
  ): Promise<any> {
    return apiClient.get(`${OS_API.HUMAN_LOOP}${mentorId}/availability/slots/`, {
      params: {
        date,
        service_id: serviceId,
      },
    });
  }
}

export const sessionService = new SessionService();
