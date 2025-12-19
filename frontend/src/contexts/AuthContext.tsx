import React, {
  createContext,
  useContext,
  useEffect,
  ReactNode,
} from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '../store';
import { User } from '../types';
import {
  loginUser,
  initAuth,
  logout as logoutAction,
} from '../store/slices/authSlice';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const dispatch = useDispatch<AppDispatch>();

  const {
    user,
    loading,
    isAuthenticated,
    authLoaded,
  } = useSelector((state: RootState) => state.auth);

  // 🔁 Initialize auth on app load
  useEffect(() => {
    if (!authLoaded) {
      dispatch(initAuth());
    }
  }, [authLoaded, dispatch]);

  // 🔐 Login (identifier = email | username)
  const login = async (identifier: string, password: string) => {
    await dispatch(loginUser({ identifier, password })).unwrap();
  };

  // 🚪 Logout
  const logout = () => {
    dispatch(logoutAction());
  };

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
