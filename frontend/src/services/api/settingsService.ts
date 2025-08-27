import apiClient from './client';

export interface UserSettings {
  theme: 'light' | 'dark';
  language: string;
  notifications: {
    email: boolean;
    push: boolean;
    desktop: boolean;
  };
  accessibility: {
    fontSize: number;
    contrast: 'normal' | 'high';
    reducedMotion: boolean;
  };
  privacy: {
    shareProfile: boolean;
    showOnlineStatus: boolean;
  };
  display: {
    sidebarCollapsed: boolean;
    denseMode: boolean;
    listView: boolean;
  };
}

class SettingsService {
  async getUserSettings(): Promise<UserSettings> {
    try {
      const response = await apiClient.get('/api/settings/');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch user settings:', error);
      // Return default settings if API fails
      return this.getDefaultSettings();
    }
  }

  async updateUserSettings(settings: Partial<UserSettings>): Promise<UserSettings> {
    try {
      const response = await apiClient.patch('/api/settings/', settings);
      return response.data;
    } catch (error) {
      console.error('Failed to update user settings:', error);
      throw new Error('Failed to save settings');
    }
  }

  async resetToDefaults(): Promise<UserSettings> {
    try {
      const response = await apiClient.post('/api/settings/reset/');
      return response.data;
    } catch (error) {
      console.error('Failed to reset settings:', error);
      throw new Error('Failed to reset settings');
    }
  }

  getDefaultSettings(): UserSettings {
    return {
      theme: 'light',
      language: 'en',
      notifications: {
        email: true,
        push: true,
        desktop: true,
      },
      accessibility: {
        fontSize: 16,
        contrast: 'normal',
        reducedMotion: false,
      },
      privacy: {
        shareProfile: true,
        showOnlineStatus: true,
      },
      display: {
        sidebarCollapsed: false,
        denseMode: false,
        listView: false,
      },
    };
  }

  // Local storage fallback for offline functionality
  saveToLocalStorage(settings: UserSettings): void {
    try {
      localStorage.setItem('userSettings', JSON.stringify(settings));
    } catch (error) {
      console.error('Failed to save settings to localStorage:', error);
    }
  }

  loadFromLocalStorage(): UserSettings | null {
    try {
      const stored = localStorage.getItem('userSettings');
      return stored ? JSON.parse(stored) : null;
    } catch (error) {
      console.error('Failed to load settings from localStorage:', error);
      return null;
    }
  }
}

const settingsService = new SettingsService();
export default settingsService; 