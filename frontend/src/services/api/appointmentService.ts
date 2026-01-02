import apiClient from './client';
import { OS_API } from '../../os/apiPaths';

/* =====================================================
 * Types
 * ===================================================== */

/**
 * NEW – Slot locking / booking flow
 */
export interface LockSlotPayload {
  appointment_id?: number;
  action?: 'cancel';
  time_slot_id?: number;
  service_id?: number;
  title?: string;
  description?: string;
  cancel_reason?: string;
}

/**
 * LEGACY – old appointment creation
 * ⚠️ DO NOT USE IN NEW PAGES
 */
export interface CreateAppointmentPayload {
  mentor: number;
  date: string;   // yyyy-MM-dd
  time: string;   // HH:mm
  notes?: string;
}

/**
 * Appointment query params
 */
export interface AppointmentQuery {
  status?: 'pending' | 'confirmed' | 'completed' | 'expired' | 'cancelled';
  upcoming?: 'true' | 'false';
}

/* =====================================================
 * AppointmentService
 * ===================================================== */

class AppointmentService {
  /* ---------------------------------------------
   * 🔒 NEW – Slot based booking (CURRENT SYSTEM)
   * -------------------------------------------*/

  /**
   * Lock a time slot and create (or reuse) a pending appointment
   */
  async lockSlot(data: LockSlotPayload): Promise<any> {
    const response = await apiClient.post(
      `${OS_API.DECISION_SLOTS}lock-slot/`,
      data
    );
    return response.data;
  }

  /**
   * Check appointment lock status (countdown / expired repair)
   */
  async getLockStatus(appointmentId: number): Promise<any> {
    const response = await apiClient.get(
      `${OS_API.DECISION_SLOTS}lock-status/${appointmentId}/`
    );
    return response.data;
  }

  /**
   * Get current user's appointments (used by Upcoming / Past pages)
   */
  async getMyAppointments(
    params?: AppointmentQuery
  ): Promise<any[]> {
    const response = await apiClient.get(
      `${OS_API.DECISION_SLOTS}appointments/`,
      { params }
    );
    return response.data;
  }

  /**
   * Get appointments (alias for getMyAppointments)
   */
  async getAppointments(
    params?: AppointmentQuery
  ): Promise<any[]> {
    return this.getMyAppointments(params);
  }

  /**
   * Get appointment detail
   */
  async getAppointmentById(id: number): Promise<any> {
    const response = await apiClient.get(
      `${OS_API.DECISION_SLOTS}appointments/${id}/`
    );
    return response.data;
  }

  /**
   * Get appointment stats for current user (mentor or student)
   */
  async getAppointmentStats(): Promise<any> {
    const response = await apiClient.get(
      `${OS_API.DECISION_SLOTS}stats/`
    );
    return response.data;
  }

  /**
   * Get mentor's appointments
   */
  async getMentorAppointments(): Promise<any[]> {
    const response = await apiClient.get(
      `${OS_API.DECISION_SLOTS}mentor/appointments/`
    );
    return response.data;
  }

  /**
   * Mentor updates appointment status
   */
  async updateMentorAppointmentStatus(
    id: number,
    data: { status?: string; meeting_link?: string; meeting_platform?: string; meeting_notes?: string }
  ): Promise<any> {
    const response = await apiClient.patch(
      `${OS_API.DECISION_SLOTS}mentor/appointments/${id}/status/`,
      data
    );
    return response.data;
  }

  /**
   * Get appointment requests
   */
  async getAppointmentRequests(): Promise<any[]> {
    const response = await apiClient.get(
      `${OS_API.DECISION_SLOTS}requests/`
    );
    return response.data;
  }

  /**
   * Respond to appointment request
   */
  async respondAppointmentRequest(
    id: number,
    data: { status: 'accepted' | 'rejected'; response?: string; suggested_time_slots?: any[] }
  ): Promise<any> {
    const response = await apiClient.post(
      `${OS_API.DECISION_SLOTS}requests/${id}/respond/`,
      data
    );
    return response.data;
  }

  /**
   * Get mentor time slots within date range
   */
  async getMentorTimeSlots(params: { mentor_id: number; from: string; to: string }): Promise<any[]> {
    const response = await apiClient.get(
      `${OS_API.DECISION_SLOTS}time-slots/`,
      { params }
    );
    return response.data?.results || response.data || [];
  }

  /**
   * Create mentor time slot(s)
   */
  async createTimeSlot(data: {
    start_time: string;
    end_time: string;
    is_available?: boolean;
    is_recurring?: boolean;
    recurring_pattern?: string;
    max_bookings?: number;
    price: number;
    currency?: string;
  }): Promise<any> {
    const response = await apiClient.post(
      `${OS_API.DECISION_SLOTS}time-slots/create/`,
      data
    );
    return response.data;
  }

  /**
   * Update a time slot
   */
  async updateTimeSlot(id: number, data: { is_available?: boolean }): Promise<any> {
    const response = await apiClient.patch(
      `${OS_API.DECISION_SLOTS}time-slots/${id}/`,
      data
    );
    return response.data;
  }

  /**
   * Cancel appointment
   */
  async cancelAppointment(
    id: number,
    reason?: string
  ): Promise<any> {
    const response = await apiClient.post(
      `${OS_API.DECISION_SLOTS}appointments/${id}/cancel/`,
      { reason }
    );
    return response.data;
  }

  /**
   * Rate appointment (after completed)
   */
  async rateAppointment(
    id: number,
    rating: number,
    feedback?: string
  ): Promise<any> {
    const response = await apiClient.post(
      `${OS_API.DECISION_SLOTS}appointments/${id}/rate/`,
      { rating, feedback }
    );
    return response.data;
  }

  /* ---------------------------------------------
   * ⚠️ LEGACY – OLD APPOINTMENT FLOW
   * DO NOT USE IN NEW CODE
   * -------------------------------------------*/

  /**
   * Legacy: get appointments
   */
  async getAppointmentsLegacy(params?: any): Promise<any> {
    const response = await apiClient.get(
      `${OS_API.DECISION_SLOTS}appointments/`,
      { params }
    );
    return response.data;
  }

  /**
   * Legacy: create appointment (OLD PAGES)
   */
  async createAppointmentLegacy(
    data: CreateAppointmentPayload
  ): Promise<any> {
    const response = await apiClient.post(
      `${OS_API.DECISION_SLOTS}appointments/`,
      data
    );
    return response.data;
  }

  /**
   * ❗ Legacy alias – DO NOT REMOVE YET
   * This exists ONLY to keep old pages working.
   */
  async createAppointment(
    data: CreateAppointmentPayload
  ): Promise<any> {
    return this.createAppointmentLegacy(data);
  }
}

/* =====================================================
 * Export singleton
 * ===================================================== */

const appointmentService = new AppointmentService();
export default appointmentService;
