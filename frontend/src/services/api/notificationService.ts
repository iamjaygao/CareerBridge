import apiClient from './client';
import { OS_API } from '../../os/apiPaths';

export interface Notification {
  id: number;
  notification_type: string;
  notification_type_display?: string;
  title: string;
  message?: string;
  is_read: boolean;
  is_sent?: boolean;
  priority?: 'low' | 'normal' | 'medium' | 'high' | 'critical' | 'urgent';
  priority_display?: string;
  target_role?: 'superadmin' | 'admin' | 'staff' | 'mentor' | 'student';
  target_role_display?: string;
  related_appointment?: number | null;
  related_resume?: number | null;
  related_mentor?: number | null;
  sent_at?: string | null;
  read_at?: string | null;
  created_at: string;
  payload?: { action?: string; appointment_id?: number; [key: string]: any };
}

export interface PaginatedNotifications {
  count: number;
  next: string | null;
  previous: string | null;
  results: Notification[];
}

/**
 * Get all notifications for the current user
 */
export const getNotifications = async (params?: {
  notification_type?: string;
  is_read?: boolean;
  priority?: string;
  limit?: number;
}): Promise<PaginatedNotifications> => {
  const response = await apiClient.get<PaginatedNotifications>(OS_API.SIGNAL_DELIVERY, { params });
  return response.data;
};

/**
 * Get a single notification by ID
 */
export const getNotification = async (id: number): Promise<Notification> => {
  const response = await apiClient.get<Notification>(`${OS_API.SIGNAL_DELIVERY}${id}/`);
  return response.data;
};

/**
 * Mark one or more notifications as read
 */
export const markNotificationsAsRead = async (notificationIds: number[]): Promise<{ message: string }> => {
  const response = await apiClient.post<{ message: string }>(`${OS_API.SIGNAL_DELIVERY}mark-read/`, {
    notification_ids: notificationIds,
  });
  return response.data;
};

/**
 * Mark all notifications as read
 */
export const markAllNotificationsAsRead = async (): Promise<{ message: string }> => {
  const response = await apiClient.post<{ message: string }>(`${OS_API.SIGNAL_DELIVERY}mark-all-read/`);
  return response.data;
};

/**
 * Delete a notification
 */
export const deleteNotification = async (id: number): Promise<void> => {
  await apiClient.delete(`${OS_API.SIGNAL_DELIVERY}${id}/delete/`);
};

/**
 * Delete all notifications
 */
export const deleteAllNotifications = async (): Promise<{ message: string }> => {
  const response = await apiClient.post<{ message: string }>(`${OS_API.SIGNAL_DELIVERY}delete-all/`);
  return response.data;
};

/**
 * Get unread notification count
 */
export const getUnreadNotificationCount = async (): Promise<number> => {
  const response = await apiClient.get<{ unread_count: number }>(`${OS_API.SIGNAL_DELIVERY}unread-count/`);
  return response.data.unread_count;
};

