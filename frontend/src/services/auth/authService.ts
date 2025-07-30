import apiClient from '../api/client';
import { LoginRequest, LoginResponse, RegisterRequest, User, PasswordChangeRequest } from '../../types';

class AuthService {
  // Login
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/users/login/', credentials);
    
    // Store tokens and user data
    localStorage.setItem('access_token', response.access);
    localStorage.setItem('refresh_token', response.refresh);
    localStorage.setItem('user', JSON.stringify(response.user));
    
    return response;
  }

  // Register
  async register(userData: RegisterRequest): Promise<{ message: string }> {
    return await apiClient.post<{ message: string }>('/users/register/', userData);
  }

  // Get current user
  async getCurrentUser(): Promise<User> {
    return await apiClient.get<User>('/users/me/');
  }

  // Update user profile
  async updateProfile(userData: Partial<User>): Promise<{ message: string }> {
    return await apiClient.put<{ message: string }>('/users/me/', userData);
  }

  // Change password
  async changePassword(passwordData: PasswordChangeRequest): Promise<{ message: string }> {
    return await apiClient.post<{ message: string }>('/users/change-password/', passwordData);
  }

  // Request password reset
  async requestPasswordReset(email: string): Promise<{ message: string }> {
    return await apiClient.post<{ message: string }>('/users/password-reset-request/', { email });
  }

  // Reset password
  async resetPassword(token: string, newPassword: string, newPasswordConfirm: string): Promise<{ message: string }> {
    return await apiClient.post<{ message: string }>(`/users/reset-password/${token}/`, {
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
    });
  }

  // Upload avatar
  async uploadAvatar(file: File): Promise<{ message: string; avatar_url: string }> {
    return await apiClient.upload<{ message: string; avatar_url: string }>('/users/avatar/', file);
  }

  // Logout
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }

  // Get stored user data
  getStoredUser(): User | null {
    const userData = localStorage.getItem('user');
    return userData ? JSON.parse(userData) : null;
  }

  // Get access token
  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  // Get refresh token
  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }
}

export const authService = new AuthService();
export default authService; 