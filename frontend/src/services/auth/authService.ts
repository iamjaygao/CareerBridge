import apiClient from '../api/client';
import { User } from '../../types';

interface LoginResponse {
  access: string;
  refresh?: string;
  user: User;
}

interface LoginCredentials {
  identifier: string;
  password: string;
}

class AuthService {
  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await apiClient.post('/users/login/', credentials);
      const { user, tokens } = response.data;
      const { access, refresh } = tokens || {};
      
      // Store tokens
      if (access) {
        localStorage.setItem('access_token', access);
      }
      if (refresh) {
        localStorage.setItem('refresh_token', refresh);
      }
      
      // Store user
      if (user) {
        localStorage.setItem('user', JSON.stringify(user));
      }
      
      return { access, refresh, user };
    } catch (error: any) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  /**
   * Register new user
   */
  async register(userData: {
    username: string;
    email: string;
    password: string;
    password_confirm?: string;
  }): Promise<any> {
    try {
      const response = await apiClient.post('/users/register/', userData);
      return response.data;
    } catch (error: any) {
      console.error('Registration failed:', error);
      throw error;
    }
  }

  /**
   * Logout user
   */
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<string> {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await apiClient.post('/users/refresh/', {
        refresh: refreshToken,
      });

      const { access } = response.data;
      localStorage.setItem('access_token', access);
      return access;
    } catch (error: any) {
      console.error('Token refresh failed:', error);
      this.logout();
      throw error;
    }
  }

  /**
   * Get stored user from localStorage
   */
  getStoredUser(): User | null {
    try {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('Failed to get stored user:', error);
      return null;
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }

  /**
   * Check if token needs refresh (simple check - token exists)
   */
  needsTokenRefresh(): boolean {
    // In a real app, you'd decode the JWT and check expiration
    // For now, just check if token exists
    return !!localStorage.getItem('access_token');
  }

  /**
   * Update user profile
   */
  async updateProfile(userData: Partial<User>): Promise<User> {
    try {
      const response = await apiClient.put('/users/me/', userData);
      
      const updatedUser = response.data;
      localStorage.setItem('user', JSON.stringify(updatedUser));
      return updatedUser;
    } catch (error: any) {
      console.error('Profile update failed:', error);
      throw error;
    }
  }

  /**
   * Upload user avatar
   */
  async uploadAvatar(file: File): Promise<{ avatar_url?: string }> {
    try {
      const formData = new FormData();
      formData.append('avatar', file);
      const response = await apiClient.post('/users/avatar/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error: any) {
      console.error('Avatar upload failed:', error);
      throw error;
    }
  }

  /**
   * Change password
   */
  async changePassword(payload: {
    old_password: string;
    new_password: string;
    new_password_confirm: string;
  }): Promise<any> {
    try {
      const response = await apiClient.post('/users/change-password/', payload);
      return response.data;
    } catch (error: any) {
      console.error('Password change failed:', error);
      throw error;
    }
  }

  /**
   * Check username change availability
   */
  async getUsernameChangeStatus(): Promise<{ can_change: boolean; days_left: number }> {
    try {
      const response = await apiClient.get('/users/username-change-status/');
      return response.data;
    } catch (error: any) {
      console.error('Failed to get username change status:', error);
      throw error;
    }
  }

  /**
   * Resend email verification
   */
  async resendVerification(email: string): Promise<any> {
    try {
      const response = await apiClient.post('/users/resend-verification/', { email });
      return response.data;
    } catch (error: any) {
      console.error('Resend verification failed:', error);
      throw error;
    }
  }

  /**
   * Confirm email verification
   */
  async confirmEmailVerification(token: string): Promise<any> {
    try {
      const response = await apiClient.post('/users/verify-email/', { token });
      return response.data;
    } catch (error: any) {
      console.error('Email verification failed:', error);
      throw error;
    }
  }

  /**
   * Request email verification
   */
  async requestEmailVerification(email: string): Promise<any> {
    try {
      const response = await apiClient.post('/users/request-verification/', { email });
      return response.data;
    } catch (error: any) {
      console.error('Email verification request failed:', error);
      throw error;
    }
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<any> {
    try {
      const response = await apiClient.post('/users/password-reset/', { email });
      return response.data;
    } catch (error: any) {
      console.error('Password reset request failed:', error);
      throw error;
    }
  }

  /**
   * Reset password with token
   */
  async resetPassword(
    token: string,
    newPassword: string,
    newPasswordConfirm: string
  ): Promise<any> {
    try {
      const response = await apiClient.post('/users/password-reset/confirm/', {
        token,
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      });
      return response.data;
    } catch (error: any) {
      console.error('Password reset failed:', error);
      throw error;
    }
  }
}

const authService = new AuthService();
export default authService;
