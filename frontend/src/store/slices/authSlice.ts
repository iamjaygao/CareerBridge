import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { REHYDRATE } from 'redux-persist';
import axios from 'axios';

// Get API URL from env
// .env has: REACT_APP_API_URL=http://127.0.0.1:8001/api/v1
// So we use it directly without adding /api/v1 again
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001/api/v1';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  avatar?: string;
  first_name?: string;
  last_name?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  authLoaded: boolean;
  loading: boolean;
  error: string | null;
}

// Safely load initial state from localStorage
const storedToken = localStorage.getItem('access_token');
const storedUser = localStorage.getItem('user');

let parsedUser = null;
if (storedUser) {
  try {
    parsedUser = JSON.parse(storedUser);
  } catch (error) {
    console.error('Failed to parse stored user:', error);
    // Clear invalid user data
    localStorage.removeItem('user');
  }
}

const initialState: AuthState = {
  user: parsedUser,
  token: storedToken,
  isAuthenticated: !!storedToken,
  authLoaded: false, // Set to true after reading from localStorage
  loading: false,
  error: null,
};

// Async thunks
export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials: { login: string; password: string }, { rejectWithValue }) => {
    try {
      console.log('Login request to:', `${API_BASE_URL}/users/login/`);
      const response = await axios.post(`${API_BASE_URL}/users/login/`, credentials, {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 10000,
      });
      const { access, refresh, user } = response.data;
      
      // Store tokens and user in localStorage
      localStorage.setItem('access_token', access);
      if (refresh) {
        localStorage.setItem('refresh_token', refresh);
      }
      if (user) {
        localStorage.setItem('user', JSON.stringify(user));
      }
      
      return { access, refresh, user };
    } catch (error: any) {
      console.error('Login error:', error);
      // Handle network errors
      if (error.code === 'ECONNABORTED' || error.message === 'Network Error' || !error.response) {
        return rejectWithValue('Network error: Unable to connect to the server. Please check if the backend is running on http://localhost:8001');
      }
      // Handle API errors
      const errorMessage = error.response?.data?.non_field_errors?.[0] 
        || error.response?.data?.message 
        || error.response?.data?.detail
        || 'Login failed. Please check your credentials.';
      return rejectWithValue(errorMessage);
    }
  }
);

export const registerUser = createAsyncThunk(
  'auth/register',
  async (userData: { username: string; email: string; password: string }) => {
    const response = await axios.post(`${API_BASE_URL}/users/register/`, userData);
    return response.data;
  }
);

export const fetchUserProfile = createAsyncThunk(
  'auth/fetchProfile',
  async (_, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        return rejectWithValue('No access token available');
      }
      const response = await axios.get(`${API_BASE_URL}/users/me/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    } catch (error: any) {
      console.error('Failed to fetch user profile:', error);
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch user profile');
    }
  }
);

// Initialize auth state on app start - verifies token and loads user
export const initAuth = createAsyncThunk(
  'auth/init',
  async (_, { dispatch, rejectWithValue }) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        // No token, ensure state is cleared
        return { user: null, token: null, isAuthenticated: false };
      }

      // Try to fetch user profile to verify token is valid
      try {
        const userData = await dispatch(fetchUserProfile()).unwrap();
        return { user: userData, token, isAuthenticated: true };
      } catch (profileError) {
        // Token might be expired, try to refresh
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          try {
            const response = await axios.post(`${API_BASE_URL}/users/refresh/`, {
              refresh: refreshToken,
            });
            const { access } = response.data;
            localStorage.setItem('access_token', access);
            
            // Retry fetching profile with new token
            const userData = await dispatch(fetchUserProfile()).unwrap();
            return { user: userData, token: access, isAuthenticated: true };
          } catch (refreshError) {
            // Refresh failed, clear auth
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            return { user: null, token: null, isAuthenticated: false };
          }
        } else {
          // No refresh token, clear auth
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
          return { user: null, token: null, isAuthenticated: false };
        }
      }
    } catch (error: any) {
      console.error('Auth initialization failed:', error);
      return rejectWithValue('Failed to initialize auth');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      // Clear localStorage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      
      // Reset Redux state
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      state.authLoaded = true; // Keep authLoaded true after logout
      state.error = null;
    },
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
      state.isAuthenticated = true;
    },
    updateToken: (state, action: PayloadAction<string>) => {
      state.token = action.payload;
      state.isAuthenticated = !!action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(REHYDRATE, (state, action: any) => {
        // If persisted state exists, use it
        if (action.payload?.auth) {
          state.user = action.payload.auth.user;
          state.token = action.payload.auth.token;
          state.isAuthenticated = !!action.payload.auth.token;
        } else {
          // Fall back to localStorage if persisted state is empty (first load)
          const storedToken = localStorage.getItem('access_token');
          const storedUser = localStorage.getItem('user');
          
          if (storedToken) {
            state.token = storedToken;
            state.isAuthenticated = true;
            
            if (storedUser) {
              try {
                state.user = JSON.parse(storedUser);
              } catch (error) {
                console.error('Failed to parse stored user during rehydration:', error);
                state.user = null;
              }
            }
          } else {
            // No token in localStorage, ensure state is cleared
            state.user = null;
            state.token = null;
            state.isAuthenticated = false;
          }
        }
        // Always set authLoaded to true after rehydration completes
        state.authLoaded = true;
      })
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.token = action.payload.access;
        state.user = action.payload.user;
        state.isAuthenticated = true;
        state.error = null;

        // Ensure localStorage is updated (already done in thunk, but keep for consistency)
        localStorage.setItem('access_token', action.payload.access);
        if (action.payload.refresh) {
          localStorage.setItem('refresh_token', action.payload.refresh);
        }
        if (action.payload.user) {
          localStorage.setItem('user', JSON.stringify(action.payload.user));
        }
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error = (action.payload as string) || action.error.message || 'Login failed';
      })
      .addCase(fetchUserProfile.fulfilled, (state, action) => {
        state.user = action.payload;
        state.isAuthenticated = true;
        // Update localStorage with fresh user data
        if (action.payload) {
          localStorage.setItem('user', JSON.stringify(action.payload));
        }
      })
      .addCase(fetchUserProfile.rejected, (state) => {
        // If profile fetch fails, token might be invalid
        // Don't clear state here - let initAuth handle it
        state.error = 'Failed to fetch user profile';
      })
      .addCase(initAuth.pending, (state) => {
        state.loading = true;
      })
      .addCase(initAuth.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.isAuthenticated = action.payload.isAuthenticated;
        state.authLoaded = true;
        state.error = null;
      })
      .addCase(initAuth.rejected, (state) => {
        state.loading = false;
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
        state.authLoaded = true;
      });
  },
});

export const { logout, setUser, updateToken, clearError } = authSlice.actions;
export const clearUser = logout; // Alias for compatibility
// loginUser, registerUser, and fetchUserProfile are already exported above
export default authSlice.reducer;

