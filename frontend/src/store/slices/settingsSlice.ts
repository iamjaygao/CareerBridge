import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SettingsState {
  theme: 'light' | 'dark';
  language: string;
  notifications: {
    email: boolean;
    push: boolean;
    sms: boolean;
    appointmentReminders: boolean;
    paymentNotifications: boolean;
    desktop: boolean;
  };
  accessibility: {
    fontSize: number;
    highContrast: boolean;
    screenReader: boolean;
    reducedMotion: boolean;
    contrast: string;
  };
  privacy: {
    profileVisibility: boolean;
    dataSharing: boolean;
    analytics: boolean;
    showOnlineStatus: boolean;
    shareProfile: boolean;
  };
  display: {
    compactMode: boolean;
    showAvatars: boolean;
    denseMode: boolean;
    listView: boolean;
    sidebarCollapsed: boolean;
  };
}

const initialState: SettingsState = {
  theme: 'light',
  language: 'en',
  notifications: {
    email: true,
    push: true,
    sms: false,
    appointmentReminders: true,
    paymentNotifications: true,
    desktop: true,
  },
  accessibility: {
    fontSize: 14,
    highContrast: false,
    screenReader: false,
    reducedMotion: false,
    contrast: 'normal',
  },
  privacy: {
    profileVisibility: true,
    dataSharing: false,
    analytics: true,
    showOnlineStatus: true,
    shareProfile: true,
  },
  display: {
    compactMode: false,
    showAvatars: true,
    denseMode: false,
    listView: false,
    sidebarCollapsed: false,
  },
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
    },
    setLanguage: (state, action: PayloadAction<string>) => {
      state.language = action.payload;
    },
    setNotificationSettings: (state, action: PayloadAction<Partial<SettingsState['notifications']>>) => {
      state.notifications = { ...state.notifications, ...action.payload };
    },
    setAccessibilitySettings: (state, action: PayloadAction<Partial<SettingsState['accessibility']>>) => {
      state.accessibility = { ...state.accessibility, ...action.payload };
    },
    setPrivacySettings: (state, action: PayloadAction<Partial<SettingsState['privacy']>>) => {
      state.privacy = { ...state.privacy, ...action.payload };
    },
    setDisplaySettings: (state, action: PayloadAction<Partial<SettingsState['display']>>) => {
      state.display = { ...state.display, ...action.payload };
    },
    resetSettings: (state) => {
      return initialState;
    },
  },
});

export const {
  setTheme,
  setLanguage,
  setNotificationSettings,
  setAccessibilitySettings,
  setPrivacySettings,
  setDisplaySettings,
  resetSettings,
} = settingsSlice.actions;

export default settingsSlice.reducer;

