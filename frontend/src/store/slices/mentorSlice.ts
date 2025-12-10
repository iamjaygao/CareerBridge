import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import apiClient from '../../services/api/client';

interface Mentor {
  id: number;
  user: {
    id: number;
    username: string;
    email: string;
    role?: 'admin' | 'mentor' | 'student' | string;
    avatar?: string;
    first_name?: string;
    last_name?: string;
  };
  expertise: string[];
  bio: string;
  rating: number;
  price_per_hour: number;
  availability: any;
}

interface MentorState {
  mentors: Mentor[];
  loading: boolean;
  error: string | null;
  filters: {
    search?: string;
    expertise?: string | string[];
    industry?: string;
    experience_level?: string;
    specialization?: string;
    minRating?: number;
    maxPrice?: number;
  };
}

const initialState: MentorState = {
  mentors: [],
  loading: false,
  error: null,
  filters: {},
};

export const fetchMentors = createAsyncThunk('mentors/fetchAll', async (filters: any = {}, { rejectWithValue }) => {
  try {
    const params = filters || {};
    const response = await apiClient.get('/mentors/', { params });
    return response.data.results || response.data;
  } catch (error: any) {
    console.error('Failed to fetch mentors:', error);
    // For 401 errors, still return empty array instead of rejecting
    // This allows visitors to see the page without errors
    if (error.response?.status === 401) {
      console.warn('Unauthorized access to mentors API, returning empty list');
      return [];
    }
    return rejectWithValue(error.response?.data?.message || 'Failed to fetch mentors');
  }
});

export const fetchMentorById = createAsyncThunk('mentors/fetchById', async (id: number) => {
  const response = await apiClient.get(`/mentors/${id}/`);
  return response.data;
});

const mentorSlice = createSlice({
  name: 'mentors',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<MentorState['filters']>) => {
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
      .addCase(fetchMentors.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMentors.fulfilled, (state, action) => {
        state.loading = false;
        state.mentors = action.payload;
      })
      .addCase(fetchMentors.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch mentors';
      });
  },
});

export const { setFilters, clearFilters, clearError } = mentorSlice.actions;
export default mentorSlice.reducer;

