import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiClient from '../services/api/client';
import { SystemSettings } from '../types';
import { canCallModule } from '../utils/phaseAGuard';

interface SystemSettingsContextType {
  settings: SystemSettings | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const SystemSettingsContext = createContext<SystemSettingsContextType | undefined>(undefined);

export const SystemSettingsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = async () => {
    // Phase-A guard: ADMINPANEL frozen for SuperAdmin world
    // SystemSettings are for userland admin only, not kernel control plane
    if (!canCallModule('ADMINPANEL')) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/adminpanel/system/settings/public/');
      setSettings(response.data);
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail 
        || err?.response?.data?.error
        || err?.message 
        || 'Failed to load system settings';
      setError(errorMessage);
      console.error('Failed to fetch system settings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  return (
    <SystemSettingsContext.Provider value={{ settings, loading, error, refresh: fetchSettings }}>
      {children}
    </SystemSettingsContext.Provider>
  );
};

export const useSystemSettings = (): SystemSettingsContextType => {
  const context = useContext(SystemSettingsContext);
  if (context === undefined) {
    throw new Error('useSystemSettings must be used within a SystemSettingsProvider');
  }
  return context;
};

