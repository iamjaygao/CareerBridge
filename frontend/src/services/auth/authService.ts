import enhancedApiClient from '../api/enhancedClient';
import { LoginRequest, LoginResponse, RegisterRequest, User, PasswordChangeRequest } from '../../types';

interface TokenRefreshResponse {
  access: string;
  refresh: string;
}



class AuthService {
  // Login
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await enhancedApiClient.post<LoginResponse>('/users/login/', credentials);
    
    // Store tokens and user data
    this.setTokens(response.access, response.refresh);
    this.setUser(response.user);
    
    return response;
  }

  // Register
  async register(userData: RegisterRequest): Promise<{ message: string }> {
    return await enhancedApiClient.post<{ message: string }>('/users/register/', userData);
  }

  // Get current user
  async getCurrentUser(): Promise<User> {
    return await enhancedApiClient.get<User>('/users/me/');
  }

  // Update user profile
  async updateProfile(userData: Partial<User>): Promise<{ message: string }> {
    return await enhancedApiClient.put<{ message: string }>('/users/me/', userData);
  }

  // Change password
  async changePassword(passwordData: PasswordChangeRequest): Promise<{ message: string }> {
    return await enhancedApiClient.post<{ message: string }>('/users/change-password/', passwordData);
  }

  // Request password reset
  async requestPasswordReset(email: string): Promise<{ message: string }> {
    return await enhancedApiClient.post<{ message: string }>('/users/password-reset-request/', { email });
  }

  // Reset password
  async resetPassword(token: string, newPassword: string, newPasswordConfirm: string): Promise<{ message: string }> {
    return await enhancedApiClient.post<{ message: string }>(`/users/reset-password/${token}/`, {
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
    });
  }

  // Upload avatar
  async uploadAvatar(file: File): Promise<{ message: string; avatar_url: string }> {
    return await enhancedApiClient.upload('/users/avatar/', file);
  }

  // Email verification
  async requestEmailVerification(email: string): Promise<{ message: string }> {
    return await enhancedApiClient.post<{ message: string }>('/users/email-verification/', { email });
  }

  // Confirm email verification
  async confirmEmailVerification(token: string): Promise<{ message: string }> {
    return await enhancedApiClient.post<{ message: string }>('/users/email-verification/confirm/', { token });
  }

  // Refresh token
  async refreshToken(): Promise<TokenRefreshResponse> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await enhancedApiClient.post<TokenRefreshResponse>('/auth/token/refresh/', {
      refresh: refreshToken,
    });

    this.setTokens(response.access, response.refresh);
    return response;
  }

  // Logout
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('token_expires_at');
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    const token = this.getAccessToken();
    const expiresAt = this.getTokenExpiresAt();
    
    if (!token || !expiresAt) {
      return false;
    }

    // Check if token is expired
    if (Date.now() > expiresAt) {
      this.logout();
      return false;
    }

    return true;
  }

  // Check if token needs refresh
  needsTokenRefresh(): boolean {
    const expiresAt = this.getTokenExpiresAt();
    if (!expiresAt) return true;

    // Refresh token 5 minutes before expiry
    const refreshThreshold = 5 * 60 * 1000; // 5 minutes
    return Date.now() > (expiresAt - refreshThreshold);
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

  // Get token expiry time
  getTokenExpiresAt(): number | null {
    const expiresAt = localStorage.getItem('token_expires_at');
    return expiresAt ? parseInt(expiresAt) : null;
  }

  // Set tokens and expiry
  private setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    
    // Set expiry time (assuming 1 hour expiry)
    const expiresAt = Date.now() + (60 * 60 * 1000); // 1 hour
    localStorage.setItem('token_expires_at', expiresAt.toString());
  }

  // Set user data
  private setUser(user: User): void {
    localStorage.setItem('user', JSON.stringify(user));
  }
}

export const authService = new AuthService();
export default authService; 