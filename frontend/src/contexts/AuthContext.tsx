import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { useDispatch } from 'react-redux';
import { User } from '../types';
import authService from '../services/auth/authService';
import { setUser, clearUser } from '../store/slices/authSlice';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (login: string, password: string) => Promise<void>;
  register: (userData: any) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  updateProfile: (userData: Partial<User>) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const dispatch = useDispatch();
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    authService.logout();
    setUserState(null);
    dispatch(clearUser());
  }, [dispatch]);

  const refreshToken = useCallback(async () => {
    try {
      await authService.refreshToken();
      const storedUser = authService.getStoredUser();
      if (storedUser) {
        setUserState(storedUser);
        dispatch(setUser(storedUser));
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      throw error;
    }
  }, [dispatch, logout]);

  // Restore authentication state from localStorage on page refresh
  const initializeAuth = useCallback(async () => {
    try {
      // Directly read from localStorage to restore state immediately
      const accessToken = localStorage.getItem('access_token');
      const userStr = localStorage.getItem('user');
      
      if (accessToken && userStr) {
        try {
          const storedUser = JSON.parse(userStr) as User;
          // Restore user state immediately (synchronously)
          setUserState(storedUser);
          dispatch(setUser(storedUser));
          
          // Optionally refresh token if needed (async, non-blocking)
          if (authService.needsTokenRefresh()) {
            try {
              await refreshToken();
            } catch (refreshError) {
              // If refresh fails, keep the existing token and user
              console.warn('Token refresh failed, using existing token:', refreshError);
            }
          }
        } catch (parseError) {
          console.error('Failed to parse stored user:', parseError);
          // Clear invalid data
          localStorage.removeItem('user');
          localStorage.removeItem('access_token');
        }
      } else if (accessToken && !userStr) {
        // Token exists but no user data - try to refresh to get user
        try {
          if (authService.needsTokenRefresh()) {
            await refreshToken();
          }
        } catch (refreshError) {
          console.error('Failed to restore user with token refresh:', refreshError);
          authService.logout();
        }
      }
    } catch (error) {
      console.error('Auth initialization failed:', error);
      authService.logout();
    } finally {
      setLoading(false);
    }
  }, [dispatch, refreshToken]);

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  const login = async (login: string, password: string) => {
    try {
      const response = await authService.login({ login, password });
      setUserState(response.user);
      dispatch(setUser(response.user));
    } catch (error) {
      throw error;
    }
  };

  const register = async (userData: any) => {
    try {
      await authService.register(userData);
    } catch (error) {
      throw error;
    }
  };

  const updateProfile = async (userData: Partial<User>) => {
    try {
      await authService.updateProfile(userData);
      if (user) {
        const updatedUser = { ...user, ...userData } as User;
        setUserState(updatedUser);
        dispatch(setUser(updatedUser));
      }
    } catch (error) {
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshToken,
    updateProfile,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 