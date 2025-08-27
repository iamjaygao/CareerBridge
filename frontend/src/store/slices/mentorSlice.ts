import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import mentorService from '../../services/api/mentorService';
import { MentorDetail } from '../../types';

interface MentorState {
  mentors: any[];
  selectedMentor: MentorDetail | null;
  loading: boolean;
  error: string | null;
  filters: any;
}

const initialState: MentorState = {
  mentors: [],
  selectedMentor: null,
  loading: false,
  error: null,
  filters: {},
};

export const fetchMentors = createAsyncThunk(
  'mentors/fetchMentors',
  async (filters?: any) => {
    return await mentorService.getMentors(filters);
  }
);

export const fetchMentorById = createAsyncThunk(
  'mentors/fetchMentorById',
  async (id: number) => {
    return await mentorService.getMentorById(id);
  }
);

const mentorSlice = createSlice({
  name: 'mentors',
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
      // Fetch mentors
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
      })

      // Fetch mentor by ID
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
        state.error = action.error.message || 'Failed to fetch mentor details';
      });
  },
});

export const { setFilters, clearFilters } = mentorSlice.actions;

export default mentorSlice.reducer;