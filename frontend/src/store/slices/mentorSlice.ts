import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import apiClient from '../../services/api/client';
import { Mentor } from '../../types';
import type { MentorFilters } from '../../types';

/**
 * Redux State
 * =========================
 * IMPORTANT:
 * - Mentor type is the SaaS-aligned Mentor from /types
 * - This must match MentorProfileSerializer output
 */

interface MentorState {
  mentors: Mentor[];
  loading: boolean;
  error: string | null;
  filters: MentorFilters;
  count: number; // ✅ total mentors count (for pagination)
}

const initialState: MentorState = {
  mentors: [],
  loading: false,
  error: null,
  filters: {},
  count: 0,
};

/**
 * Fetch mentor list
 * =========================
 * Supports:
 * - DRF paginated response: { results, count, next, previous }
 * - Non-paginated response: Mentor[]
 */
export const fetchMentors = createAsyncThunk<
  { results: Mentor[]; count: number },
  any
>('mentors/fetchAll', async (filters = {}, { rejectWithValue }) => {
  try {
    const response = await apiClient.get('/mentors/', {
      params: filters,
    });

    const data: any = response.data;

    // ✅ DRF paginated response
    if (data?.results && typeof data.count === 'number') {
      return {
        results: data.results as Mentor[],
        count: data.count,
      };
    }

    // ✅ Non-paginated fallback (dev / legacy)
    if (Array.isArray(data)) {
      return {
        results: data as Mentor[],
        count: data.length,
      };
    }

    // Safety fallback
    return {
      results: [],
      count: 0,
    };
  } catch (error: any) {
    console.error('Failed to fetch mentors:', error);

    // Visitor-safe behavior
    if (error.response?.status === 401) {
      return {
        results: [],
        count: 0,
      };
    }

    return rejectWithValue(
      error.response?.data?.message || 'Failed to fetch mentors'
    );
  }
});

/**
 * Fetch mentor detail
 * =========================
 * Used by MentorDetailPage
 */
export const fetchMentorById = createAsyncThunk<Mentor, number>(
  'mentors/fetchById',
  async (id: number) => {
    const response = await apiClient.get<Mentor>(`/mentors/${id}/`);
    return response.data;
  }
);

const mentorSlice = createSlice({
  name: 'mentors',
  initialState,
  reducers: {
    setFilters: (
      state,
      action: PayloadAction<MentorFilters>
    ) => {
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
        state.error = null;
        state.mentors = action.payload.results; // ✅ 正确
        state.count = action.payload.count;     // ✅ 正确
      })
      .addCase(fetchMentors.rejected, (state, action) => {
        state.loading = false;
        state.error =
          (action.payload as string) ||
          action.error.message ||
          'Failed to fetch mentors';
      });
  },
});

export const {
  setFilters,
  clearFilters,
  clearError,
} = mentorSlice.actions;

export default mentorSlice.reducer;
