import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { Resume, PaginatedResponse } from '../../types';
import apiClient from '../../services/api/client';

// Async thunks
export const fetchResumes = createAsyncThunk(
  'resumes/fetchResumes',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<PaginatedResponse<Resume>>('/resumes/');
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to fetch resumes');
    }
  }
);

export const uploadResume = createAsyncThunk(
  'resumes/uploadResume',
  async (file: File, { rejectWithValue }) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name);
      
      const response = await apiClient.post<Resume>('/resumes/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to upload resume');
    }
  }
);

// Resume state interface
interface ResumeState {
  resumes: Resume[];
  selectedResume: Resume | null;
  loading: boolean;
  error: string | null;
  totalCount: number;
  nextPage: string | null;
  previousPage: string | null;
}

// Initial state
const initialState: ResumeState = {
  resumes: [],
  selectedResume: null,
  loading: false,
  error: null,
  totalCount: 0,
  nextPage: null,
  previousPage: null,
};

// Resume slice
const resumeSlice = createSlice({
  name: 'resumes',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearSelectedResume: (state) => {
      state.selectedResume = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch resumes
    builder
      .addCase(fetchResumes.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchResumes.fulfilled, (state, action) => {
        state.loading = false;
        state.resumes = action.payload.results;
        state.totalCount = action.payload.count;
        state.nextPage = action.payload.next || null;
        state.previousPage = action.payload.previous || null;
      })
      .addCase(fetchResumes.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Upload resume
    builder
      .addCase(uploadResume.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(uploadResume.fulfilled, (state, action) => {
        state.loading = false;
        state.resumes.unshift(action.payload);
        state.totalCount += 1;
      })
      .addCase(uploadResume.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError, clearSelectedResume } = resumeSlice.actions;
export default resumeSlice.reducer; 