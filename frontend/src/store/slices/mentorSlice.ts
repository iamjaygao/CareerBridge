import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { MentorProfile, PaginatedResponse } from '../../types';
import apiClient from '../../services/api/client';

// Async thunks
export const fetchMentors = createAsyncThunk(
  'mentors/fetchMentors',
  async (params?: { service_type?: string; industry?: string; min_rating?: number; is_verified?: boolean }, { rejectWithValue }) => {
    try {
      const queryParams = new URLSearchParams();
      if (params?.service_type) queryParams.append('service_type', params.service_type);
      if (params?.industry) queryParams.append('industry', params.industry);
      if (params?.min_rating) queryParams.append('min_rating', params.min_rating.toString());
      if (params?.is_verified !== undefined) queryParams.append('is_verified', params.is_verified.toString());

      const response = await apiClient.get<PaginatedResponse<MentorProfile>>(`/mentors/?${queryParams}`);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to fetch mentors');
    }
  }
);

export const fetchMentorById = createAsyncThunk(
  'mentors/fetchMentorById',
  async (id: number, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<MentorProfile>(`/mentors/${id}/`);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to fetch mentor');
    }
  }
);

// Mentor state interface
interface MentorState {
  mentors: MentorProfile[];
  selectedMentor: MentorProfile | null;
  loading: boolean;
  error: string | null;
  totalCount: number;
  nextPage: string | null;
  previousPage: string | null;
}

// Initial state
const initialState: MentorState = {
  mentors: [],
  selectedMentor: null,
  loading: false,
  error: null,
  totalCount: 0,
  nextPage: null,
  previousPage: null,
};

// Mentor slice
const mentorSlice = createSlice({
  name: 'mentors',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearSelectedMentor: (state) => {
      state.selectedMentor = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch mentors
    builder
      .addCase(fetchMentors.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMentors.fulfilled, (state, action) => {
        state.loading = false;
        state.mentors = action.payload.results;
        state.totalCount = action.payload.count;
        state.nextPage = action.payload.next || null;
        state.previousPage = action.payload.previous || null;
      })
      .addCase(fetchMentors.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Fetch mentor by ID
    builder
      .addCase(fetchMentorById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMentorById.fulfilled, (state, action) => {
        state.loading = false;
        state.selectedMentor = action.payload;
      })
      .addCase(fetchMentorById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError, clearSelectedMentor } = mentorSlice.actions;
export default mentorSlice.reducer; 