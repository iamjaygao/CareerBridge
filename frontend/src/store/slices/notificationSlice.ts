import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { PaginatedResponse } from '../../types';
import apiClient from '../../services/api/client';
import { OS_API } from '../../os/apiPaths';

// Backend notification interface - matches NotificationListSerializer
interface BackendNotification {
  id: number;
  title: string;
  message?: string; // Included in updated NotificationListSerializer
  notification_type: string;
  notification_type_display?: string;
  type?: 'info' | 'success' | 'warning' | 'error'; // Legacy field
  is_read: boolean;
  priority?: 'low' | 'normal' | 'medium' | 'high' | 'critical' | 'urgent';
  priority_display?: string;
  target_role?: 'superadmin' | 'admin' | 'staff' | 'mentor' | 'student';
  target_role_display?: string;
  created_at: string;
  user_id?: number;
  payload?: { action?: string; appointment_id?: number; [key: string]: any };
}

// Async thunks
export const fetchNotifications = createAsyncThunk(
  'notifications/fetchNotifications',
  async (params: { is_read?: boolean } | undefined, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<PaginatedResponse<BackendNotification>>(OS_API.SIGNAL_DELIVERY, {
        params,
      });
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to fetch notifications');
    }
  }
);

export const markNotificationAsRead = createAsyncThunk(
  'notifications/markAsRead',
  async (notificationIds: number[], { rejectWithValue }) => {
    try {
      const response = await apiClient.post<{ message: string }>(`${OS_API.SIGNAL_DELIVERY}mark-read/`, {
        notification_ids: notificationIds,
      });
      return { notificationIds, message: response.data.message };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to mark notification as read');
    }
  }
);

export const getUnreadCount = createAsyncThunk(
  'notifications/getUnreadCount',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ unread_count: number }>(`${OS_API.SIGNAL_DELIVERY}unread-count/`);
      return response.data.unread_count;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to get unread count');
    }
  }
);

export const deleteNotification = createAsyncThunk(
  'notifications/deleteNotification',
  async (notificationId: number, { rejectWithValue }) => {
    try {
      await apiClient.delete(`${OS_API.SIGNAL_DELIVERY}${notificationId}/delete/`);
      return notificationId;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to delete notification');
    }
  }
);

// Notification state interface
interface NotificationState {
  notifications: BackendNotification[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  unreadCount: number;
  nextPage: string | null;
  previousPage: string | null;
}

// Initial state
const initialState: NotificationState = {
  notifications: [],
  loading: false,
  error: null,
  totalCount: 0,
  unreadCount: 0,
  nextPage: null,
  previousPage: null,
};

// Notification slice
const notificationSlice = createSlice({
  name: 'notifications',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    addNotification: (state, action) => {
      state.notifications.unshift(action.payload);
      state.totalCount += 1;
      if (!action.payload.is_read) {
        state.unreadCount += 1;
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch notifications
    builder
      .addCase('auth/logout', () => initialState)
      .addCase('auth/login/fulfilled', () => initialState)
      .addCase('auth/init/fulfilled', () => initialState)
      .addCase(fetchNotifications.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchNotifications.fulfilled, (state, action) => {
        state.loading = false;
        // Handle both paginated and non-paginated responses
        const responseData = action.payload.data;
        let newNotifications: BackendNotification[] = [];
        
        if (responseData.results && Array.isArray(responseData.results)) {
          // Paginated response
          newNotifications = responseData.results;
          state.nextPage = responseData.next || null;
          state.previousPage = responseData.previous || null;
        } else if (Array.isArray(responseData)) {
          // Non-paginated response (plain array)
          newNotifications = responseData;
          state.nextPage = null;
          state.previousPage = null;
        } else {
          // Fallback: empty array
          newNotifications = [];
          state.nextPage = null;
          state.previousPage = null;
        }
        
        // Merge with existing notifications instead of replacing (partial sync)
        // Preserve existing notifications that aren't in the new response
        const existingMap = new Map(state.notifications.map(n => [n.id, n]));
        const newMap = new Map(newNotifications.map(n => [n.id, n]));
        
        // Update existing notifications with new data, add new ones
        newMap.forEach((newNotif, id) => {
          existingMap.set(id, newNotif);
        });
        
        // Convert back to array and sort by created_at descending
        const mergedNotifications = Array.from(existingMap.values()).sort((a, b) => {
          const dateA = new Date(a.created_at).getTime();
          const dateB = new Date(b.created_at).getTime();
          return dateB - dateA;
        });
        
        // Update state with merged notifications
        state.notifications = mergedNotifications;
        // Update totalCount based on merged array length (client-side count)
        state.totalCount = mergedNotifications.length;
      })
      .addCase(fetchNotifications.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Mark as read
    builder
      .addCase(markNotificationAsRead.fulfilled, (state, action) => {
        action.payload.notificationIds.forEach((id) => {
          const notification = state.notifications.find(n => n.id === id);
          if (notification && !notification.is_read) {
            notification.is_read = true;
            state.unreadCount = Math.max(0, state.unreadCount - 1);
          }
        });
      });

    // Get unread count
    builder
      .addCase(getUnreadCount.fulfilled, (state, action) => {
        state.unreadCount = action.payload;
      });

    // Delete notification
    builder
      .addCase(deleteNotification.fulfilled, (state, action) => {
        const notificationId = action.payload;
        const notification = state.notifications.find(n => n.id === notificationId);
        if (notification) {
          state.notifications = state.notifications.filter(n => n.id !== notificationId);
          state.totalCount = Math.max(0, state.totalCount - 1);
          if (!notification.is_read) {
            state.unreadCount = Math.max(0, state.unreadCount - 1);
          }
        }
      });
  },
});

export const { clearError, addNotification } = notificationSlice.actions;
export default notificationSlice.reducer; 
