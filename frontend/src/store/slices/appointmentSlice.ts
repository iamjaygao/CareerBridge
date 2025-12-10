import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import apiClient from '../../services/api/client';

interface Appointment {
  id: number;
  mentor: number | any;
  user: number | any;
  date: string;
  time: string;
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled' | string;
  notes?: string;
  meeting_link?: string;
  user_feedback?: any;
  mentor_feedback?: any;
}

interface AppointmentState {
  appointments: Appointment[];
  loading: boolean;
  error: string | null;
  filters: {
    status?: string;
    dateFrom?: string;
    dateTo?: string;
    page?: number;
    sort_by?: string;
  };
}

const initialState: AppointmentState = {
  appointments: [],
  loading: false,
  error: null,
  filters: {},
};

export const fetchAppointments = createAsyncThunk('appointments/fetchAll', async (filters?: any) => {
  const response = await apiClient.get('/appointments/appointments/', { params: filters });
  return response.data.results || response.data;
});

export const createAppointment = createAsyncThunk(
  'appointments/create',
  async (data: { mentor: number; date: string; time: string; notes?: string }) => {
    const response = await apiClient.post('/appointments/appointments/', data);
    return response.data;
  }
);

export const cancelAppointment = createAsyncThunk('appointments/cancel', async (id: number) => {
  const response = await apiClient.post(`/appointments/appointments/${id}/cancel/`, {});
  return response.data;
});

export const submitFeedback = createAsyncThunk(
  'appointments/submitFeedback',
  async (data: { appointmentId: number; rating: number; comment?: string }) => {
    const response = await apiClient.post(
      `/appointments/appointments/${data.appointmentId}/feedback/`,
      {
        rating: data.rating,
        comment: data.comment,
      }
    );
    return response.data;
  }
);

const appointmentSlice = createSlice({
  name: 'appointments',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<AppointmentState['filters']>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAppointments.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAppointments.fulfilled, (state, action) => {
        state.loading = false;
        state.appointments = action.payload;
      })
      .addCase(fetchAppointments.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch appointments';
      })
      .addCase(createAppointment.fulfilled, (state, action) => {
        state.appointments.unshift(action.payload);
      })
      .addCase(submitFeedback.fulfilled, (state, action) => {
        // Update appointment with feedback if needed
        const appointment = state.appointments.find((a) => a.id === action.payload.appointment_id);
        if (appointment) {
          // Mark as having feedback
        }
      });
  },
});

export const { setFilters, clearFilters, clearError } = appointmentSlice.actions;
export default appointmentSlice.reducer;

