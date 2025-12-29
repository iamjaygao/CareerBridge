import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import apiClient from '../../services/api/client';

interface Resume {
  id: number;
  title: string;
  file: string;
  status: string;
  created_at: string;
  analyzed_at?: string;
  uploaded_at?: string;
  file_type?: string;
  file_size?: number;
  analysis_result?: any;
  analysis?: any;
}

interface ResumeState {
  resumes: Resume[];
  loading: boolean;
  error: string | null;
  selectedResume: Resume | null;
  uploadProgress: number;
}

const initialState: ResumeState = {
  resumes: [],
  loading: false,
  error: null,
  selectedResume: null,
  uploadProgress: 0,
};

export const fetchResumes = createAsyncThunk('resumes/fetchAll', async () => {
  const response = await apiClient.get('/resumes/');
  return response.data.results || response.data;
});

export const uploadResume = createAsyncThunk(
  'resumes/upload',
  async (data: { file: File; title: string }) => {
    const formData = new FormData();
    formData.append('file', data.file);
    formData.append('title', data.title);
    
    const response = await apiClient.post('/resumes/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
);

export const deleteResume = createAsyncThunk('resumes/delete', async (id: number) => {
  await apiClient.delete(`/resumes/${id}/`);
  return id;
});

export const analyzeResume = createAsyncThunk(
  'resumes/analyze',
  async (id: number) => {
    const response = await apiClient.post('/resumes/analyze/', {
      resume_id: id,
    });
    return response.data;
  }
);

const resumeSlice = createSlice({
  name: 'resumes',
  initialState,
  reducers: {
    setSelectedResume: (state, action: PayloadAction<Resume | null>) => {
      state.selectedResume = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchResumes.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchResumes.fulfilled, (state, action) => {
        state.loading = false;
        state.resumes = action.payload;
      })
      .addCase(fetchResumes.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch resumes';
      })
      .addCase(uploadResume.fulfilled, (state, action) => {
        state.resumes.unshift(action.payload);
      })
      .addCase(deleteResume.fulfilled, (state, action) => {
        state.resumes = state.resumes.filter((r) => r.id !== action.payload);
      });
  },
});

export const { setSelectedResume, clearError } = resumeSlice.actions;
export default resumeSlice.reducer;
