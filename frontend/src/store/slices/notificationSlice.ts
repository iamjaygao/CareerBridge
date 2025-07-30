import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { Notification, PaginatedResponse } from '../../types';
import apiClient from '../../services/api/client';

// Async thunks
export const fetchNotifications = createAsyncThunk(
  'notifications/fetchNotifications',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<PaginatedResponse<Notification>>('/notifications/');
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
      const response = await apiClient.post<{ message: string }>('/notifications/mark-read/', {
        notification_ids: notificationIds,
      });
      return { notificationIds, message: response.message };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to mark notification as read');
    }
  }
);

export const getUnreadCount = createAsyncThunk(
  'notifications/getUnreadCount',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ unread_count: number }>('/notifications/unread-count/');
      return response.unread_count;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to get unread count');
    }
  }
);

// Notification state interface
interface NotificationState {
  notifications: Notification[];
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
      .addCase(fetchNotifications.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchNotifications.fulfilled, (state, action) => {
        state.loading = false;
        state.notifications = action.payload.results;
        state.totalCount = action.payload.count;
        state.nextPage = action.payload.next || null;
        state.previousPage = action.payload.previous || null;
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
  },
});

export const { clearError, addNotification } = notificationSlice.actions;
export default notificationSlice.reducer; 