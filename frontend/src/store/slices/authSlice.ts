import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { REHYDRATE } from 'redux-persist';
import axios from 'axios';
import { User } from '../../types';

// =======================
// Config
// =======================
const API_BASE_URL =
  process.env.REACT_APP_API_URL || 'http://localhost:8001/api/v1';

// =======================
// Types
// =======================
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;

  authLoaded: boolean; // ⬅️ 只表示「initAuth 是否完成」
  loading: boolean;    // ⬅️ 只给 login / 用户操作用

  error: string | null;
}

// =======================
// Initial state
// =======================
const storedToken = localStorage.getItem('access_token');
const storedUser = localStorage.getItem('user');

let parsedUser: User | null = null;
if (storedUser) {
  try {
    parsedUser = JSON.parse(storedUser);
  } catch {
    localStorage.removeItem('user');
  }
}

const initialState: AuthState = {
  user: parsedUser,
  token: storedToken,
  isAuthenticated: !!storedToken,

  authLoaded: false,
  loading: false,

  error: null,
};

// =======================
// Thunks
// =======================

// 🔐 Login
export const loginUser = createAsyncThunk(
  'auth/login',
  async (
    credentials: { identifier: string; password: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/users/login/`,
        credentials,
        { headers: { 'Content-Type': 'application/json' }, timeout: 10000 }
      );

      const { user, access, refresh } = response.data;


      if (!access) {
        throw new Error('Login response missing access token');
      }

      localStorage.setItem('access_token', access);
      if (refresh) localStorage.setItem('refresh_token', refresh);
      if (user) localStorage.setItem('user', JSON.stringify(user));

      return { access, refresh, user };
    } catch (error: any) {
      if (!error.response) {
        return rejectWithValue('Network error: Unable to connect to backend.');
      }
      return rejectWithValue(
        error.response?.data?.detail ||
          error.response?.data?.message ||
          'Login failed.'
      );
    }
  }
);

// 👤 Fetch profile
export const fetchUserProfile = createAsyncThunk(
  'auth/fetchProfile',
  async (_, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return rejectWithValue('No access token');

      const response = await axios.get(`${API_BASE_URL}/users/me/`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      localStorage.setItem('user', JSON.stringify(response.data));
      return response.data;
    } catch {
      return rejectWithValue('Failed to fetch profile');
    }
  }
);

// 🔁 Init auth (APP 启动用，不影响 UI loading)
export const initAuth = createAsyncThunk(
  'auth/init',
  async (_, { dispatch }) => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return { user: null, token: null, isAuthenticated: false };
    }

    try {
      const user = await dispatch(fetchUserProfile()).unwrap();
      return { user, token, isAuthenticated: true };
    } catch {
      const refresh = localStorage.getItem('refresh_token');
      if (!refresh) {
        localStorage.clear();
        return { user: null, token: null, isAuthenticated: false };
      }

      try {
        const response = await axios.post(
          `${API_BASE_URL}/users/refresh/`,
          { refresh }
        );

        const access =
          response.data.access ?? response.data.tokens?.access;

        if (!access) throw new Error('Refresh missing access token');

        localStorage.setItem('access_token', access);
        const user = await dispatch(fetchUserProfile()).unwrap();
        return { user, token: access, isAuthenticated: true };
      } catch {
        localStorage.clear();
        return { user: null, token: null, isAuthenticated: false };
      }
    }
  }
);

// =======================
// Slice
// =======================
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      localStorage.clear();
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      state.authLoaded = true;
      state.loading = false;
      state.error = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // 🔄 Rehydrate
      .addCase(REHYDRATE, (state, action: any) => {
        if (action.payload?.auth) {
          state.user = action.payload.auth.user;
          state.token = action.payload.auth.token;
          state.isAuthenticated = !!action.payload.auth.token;
        }
        state.authLoaded = true;
      })

      // 🔐 Login（唯一会动 loading 的地方）
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.token = action.payload.access;
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

      // 👤 Profile
      .addCase(fetchUserProfile.fulfilled, (state, action) => {
        state.user = action.payload;
        state.isAuthenticated = true;
      })

      // 🔁 Init（不碰 loading）
      .addCase(initAuth.pending, (state) => {
        state.authLoaded = false;
      })
      .addCase(initAuth.fulfilled, (state, action) => {
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.isAuthenticated = action.payload.isAuthenticated;
        state.authLoaded = true;
      })
      .addCase(initAuth.rejected, (state) => {
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
        state.authLoaded = true;
      });
  },
});

export const { logout, clearError } = authSlice.actions;
export default authSlice.reducer;
