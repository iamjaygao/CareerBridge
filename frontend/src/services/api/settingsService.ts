import apiClient from './client';

// Settings interface
export interface UserSettings {
  theme?: 'light' | 'dark';
  language?: string;
  notifications?: {
    email?: boolean;
    push?: boolean;
    sms?: boolean;
    appointmentReminders?: boolean;
    paymentNotifications?: boolean;
  };
  accessibility?: {
    fontSize?: number;
    highContrast?: boolean;
    screenReader?: boolean;
  };
  privacy?: {
    profileVisibility?: boolean;
    dataSharing?: boolean;
    analytics?: boolean;
  };
  display?: {
    compactMode?: boolean;
    showAvatars?: boolean;
  };
}

class SettingsService {
  /**
   * Update user settings on the server
   */
  async updateUserSettings(settings: UserSettings): Promise<void> {
    try {
      await apiClient.put('/users/settings/', settings);
    } catch (error) {
      console.error('Failed to update user settings:', error);
      throw error;
    }
  }

  /**
   * Get user settings from the server
   */
  async getUserSettings(): Promise<UserSettings> {
    try {
      const response = await apiClient.get('/users/settings/');
      return response.data;
    } catch (error) {
      console.error('Failed to get user settings:', error);
      throw error;
    }
  }

  /**
   * Save settings to local storage (offline mode)
   */
  saveToLocalStorage(settings: UserSettings): void {
    try {
      localStorage.setItem('user_settings', JSON.stringify(settings));
    } catch (error) {
      console.error('Failed to save settings to local storage:', error);
    }
  }

  /**
   * Get settings from local storage
   */
  getFromLocalStorage(): UserSettings | null {
    try {
      const settings = localStorage.getItem('user_settings');
      return settings ? JSON.parse(settings) : null;
    } catch (error) {
      console.error('Failed to get settings from local storage:', error);
      return null;
    }
  }

  /**
   * Clear settings from local storage
   */
  clearLocalStorage(): void {
    try {
      localStorage.removeItem('user_settings');
    } catch (error) {
      console.error('Failed to clear settings from local storage:', error);
    }
  }
}

const settingsService = new SettingsService();
export default settingsService;

