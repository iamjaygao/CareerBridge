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

}

const initialState: MentorState = {
  mentors: [],
  loading: false,
  error: null,
  filters: {},
};

/**
 * Fetch mentor list
 * =========================
 * Returns SaaS Mentor list:
 * - headline
 * - job_title
 * - starting_price
 * - review_count
 * - is_verified
 * - system_role / system_insight / cta_label
 */
export const fetchMentors = createAsyncThunk<
  Mentor[],
  any
>('mentors/fetchAll', async (filters = {}, { rejectWithValue }) => {
  try {
    const response = await apiClient.get<Mentor[]>('/mentors/', {
      params: filters,
    });

    // Support both paginated & non-paginated API
    if ((response.data as any)?.results) {
      return (response.data as any).results as Mentor[];
    }

    return response.data;
  } catch (error: any) {
    console.error('Failed to fetch mentors:', error);

    // Visitor-safe behavior
    if (error.response?.status === 401) {
      return [];
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
        state.mentors = action.payload;
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
