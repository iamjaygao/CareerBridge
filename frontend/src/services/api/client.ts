import axios from 'axios';
import { assertNoLegacyApi } from '../../os/assertNoLegacyApi';
import { validateApiCall } from '../../os/probeGuard';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api/v1';

// Store reference for updating Redux state after token refresh
let storeRef: any = null;
export const setStoreRef = (store: any) => {
  storeRef = store;
};

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // GateAI OS: Warn about legacy API paths in development
    if (config.url) {
      assertNoLegacyApi(config.url);
    }
    
    // GateAI OS: Prevent write endpoints from being auto-probed
    // This catches misuse where GET requests target write-only endpoints
    if (config.url && config.method) {
      try {
        validateApiCall(config.url, config.method, 'apiClient');
      } catch (error) {
        // In production, log but don't break the app
        if (process.env.NODE_ENV === 'production') {
          console.error('[GateAI OS] Write endpoint probe blocked:', error);
          return Promise.reject(error);
        }
        // In development, throw to alert developer
        throw error;
      }
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized error
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Try to refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await apiClient.post('/users/refresh/', {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          // Update Redux state with new token if store is available
          if (storeRef) {
            try {
              storeRef.dispatch({
                type: 'auth/updateToken',
                payload: access,
              });
            } catch (error) {
              console.warn('Failed to update Redux state after token refresh:', error);
            }
          }

          // Retry the original request with the new token
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // If refresh fails, clear auth data and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;