import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SettingsState {
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

const initialState: SettingsState = {
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