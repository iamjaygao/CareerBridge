import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import resumeService, { Resume } from '../../services/api/resumeService';

interface ResumeState {
  resumes: Resume[];
  loading: boolean;
  error: string | null;
  uploadProgress: number | null;
}

const initialState: ResumeState = {
  resumes: [],
  loading: false,
  error: null,
  uploadProgress: null,
};

export const fetchResumes = createAsyncThunk(
  'resumes/fetchResumes',
  async () => {
    return await resumeService.getResumes();
  }
);

export const uploadResume = createAsyncThunk(
  'resumes/uploadResume',
  async ({ file, title }: { file: File; title?: string }) => {
    return await resumeService.uploadResume(file, title);
  }
);

export const deleteResume = createAsyncThunk(
  'resumes/deleteResume',
  async (id: number) => {
    await resumeService.deleteResume(id);
    return id;
  }
);

export const analyzeResume = createAsyncThunk(
  'resumes/analyzeResume',
  async (id: number) => {
    return await resumeService.analyzeResume(id);
  }
);

const resumeSlice = createSlice({
  name: 'resumes',
  initialState,
  reducers: {
    setUploadProgress: (state, action) => {
      state.uploadProgress = action.payload;
    },
    resetUploadProgress: (state) => {
      state.uploadProgress = null;
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
        state.resumes = action.payload;
      })
      .addCase(fetchResumes.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch resumes';
      })

    // Upload resume
      .addCase(uploadResume.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(uploadResume.fulfilled, (state, action) => {
        state.loading = false;
        state.resumes.unshift(action.payload);
        state.uploadProgress = null;
      })
      .addCase(uploadResume.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to upload resume';
        state.uploadProgress = null;
      })

    // Delete resume
      .addCase(deleteResume.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteResume.fulfilled, (state, action) => {
        state.loading = false;
        state.resumes = state.resumes.filter(resume => resume.id !== action.payload);
      })
      .addCase(deleteResume.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to delete resume';
      })

    // Analyze resume
      .addCase(analyzeResume.pending, (state, action) => {
        const resume = state.resumes.find(r => r.id === action.meta.arg);
        if (resume) {
          resume.status = 'analyzing';
        }
      })
      .addCase(analyzeResume.fulfilled, (state, action) => {
        const index = state.resumes.findIndex(r => r.id === action.payload.id);
        if (index !== -1) {
          state.resumes[index] = action.payload;
        }
      })
      .addCase(analyzeResume.rejected, (state, action) => {
        const resume = state.resumes.find(r => r.id === action.meta.arg);
        if (resume) {
          resume.status = 'failed';
        }
        state.error = action.error.message || 'Failed to analyze resume';
      });
  },
});

export const { setUploadProgress, resetUploadProgress } = resumeSlice.actions;

export default resumeSlice.reducer;