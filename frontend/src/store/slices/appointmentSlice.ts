import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import appointmentService, { AppointmentFilters, FeedbackData } from '../../services/api/appointmentService';
import { Appointment } from '../../types';

interface AppointmentState {
  appointments: Appointment[];
  selectedAppointment: Appointment | null;
  loading: boolean;
  error: string | null;
  filters: AppointmentFilters;
}

const initialState: AppointmentState = {
  appointments: [],
  selectedAppointment: null,
  loading: false,
  error: null,
  filters: {},
};

export const fetchAppointments = createAsyncThunk(
  'appointments/fetchAppointments',
  async (filters?: AppointmentFilters) => {
    return await appointmentService.getAppointments(filters);
  }
);

export const fetchAppointmentById = createAsyncThunk(
  'appointments/fetchAppointmentById',
  async (id: number) => {
    return await appointmentService.getAppointmentById(id);
  }
);

export const createAppointment = createAsyncThunk(
  'appointments/createAppointment',
  async (data: {
    mentor_id: number;
    service_id: number;
    scheduled_date: string;
    scheduled_time: string;
    user_notes?: string;
  }) => {
    return await appointmentService.createAppointment(data);
  }
);

export const cancelAppointment = createAsyncThunk(
  'appointments/cancelAppointment',
  async (id: number) => {
    await appointmentService.cancelAppointment(id);
    return id;
  }
);

export const rescheduleAppointment = createAsyncThunk(
  'appointments/rescheduleAppointment',
  async ({ id, data }: { id: number; data: { scheduled_start: string; scheduled_end: string } }) => {
    return await appointmentService.rescheduleAppointment(id, data);
  }
);

export const submitFeedback = createAsyncThunk(
  'appointments/submitFeedback',
  async ({ id, feedback }: { id: number; feedback: FeedbackData }) => {
    return await appointmentService.submitFeedback(id, feedback);
  }
);

const appointmentSlice = createSlice({
  name: 'appointments',
  initialState,
  reducers: {
    setFilters: (state, action) => {
      state.filters = action.payload;
    },
    clearFilters: (state) => {
      state.filters = {};
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch appointments
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

      // Fetch appointment by ID
      .addCase(fetchAppointmentById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAppointmentById.fulfilled, (state, action) => {
        state.loading = false;
        state.selectedAppointment = action.payload as any;
      })
      .addCase(fetchAppointmentById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch appointment details';
      })

      // Create appointment
      .addCase(createAppointment.fulfilled, (state, action) => {
        state.appointments.unshift(action.payload as any);
      })

      // Cancel appointment
      .addCase(cancelAppointment.fulfilled, (state, action) => {
        const appointment = state.appointments.find(apt => apt.id === action.payload);
        if (appointment) {
          appointment.status = 'cancelled';
        }
      })

      // Reschedule appointment
      .addCase(rescheduleAppointment.fulfilled, (state, action) => {
        const index = state.appointments.findIndex(apt => apt.id === action.payload.id);
        if (index !== -1) {
          state.appointments[index] = action.payload as any;
        }
      })

      // Submit feedback
      .addCase(submitFeedback.fulfilled, (state, action) => {
        const index = state.appointments.findIndex(apt => apt.id === action.payload.id);
        if (index !== -1) {
          state.appointments[index] = action.payload as any;
        }
      });
  },
});

export const { setFilters, clearFilters } = appointmentSlice.actions;

export default appointmentSlice.reducer;