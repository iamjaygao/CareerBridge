import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Switch,
  FormControlLabel,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Grid,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Storage as StorageIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';

import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import adminService from '../../services/api/adminService';

interface SystemSettings {
  general: {
    site_name: string;
    site_description: string;
    contact_email: string;
    support_phone: string;
    timezone: string;
    date_format: string;
    maintenance_mode: boolean;
  };
  security: {
    session_timeout: number;
    max_login_attempts: number;
    password_min_length: number;
    require_2fa: boolean;
    enable_captcha: boolean;
    allowed_file_types: string[];
    max_file_size: number;
  };
  notifications: {
    email_notifications: boolean;
    sms_notifications: boolean;
    push_notifications: boolean;
    admin_notifications: boolean;
    notification_frequency: string;
  };
  performance: {
    cache_enabled: boolean;
    cache_duration: number;
    compression_enabled: boolean;
    cdn_enabled: boolean;
    max_upload_size: number;
  };
}

const SystemSettingsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [settings, setSettings] = useState<SystemSettings>({
    general: {
      site_name: 'CareerBridge',
      site_description: 'Professional mentoring platform',
      contact_email: 'admin@careerbridge.com',
      support_phone: '+1-555-0123',
      timezone: 'UTC',
      date_format: 'MM/DD/YYYY',
      maintenance_mode: false,
    },
    security: {
      session_timeout: 30,
      max_login_attempts: 5,
      password_min_length: 8,
      require_2fa: false,
      enable_captcha: true,
      allowed_file_types: ['pdf', 'doc', 'docx', 'jpg', 'png'],
      max_file_size: 10,
    },
    notifications: {
      email_notifications: true,
      sms_notifications: false,
      push_notifications: true,
      admin_notifications: true,
      notification_frequency: 'immediate',
    },
    performance: {
      cache_enabled: true,
      cache_duration: 3600,
      compression_enabled: true,
      cdn_enabled: false,
      max_upload_size: 10,
    },
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual system settings API
      // For now, we'll use default settings since the backend doesn't have a specific settings endpoint
      console.log('Loading system settings...');
    } catch (err) {
      setError('Failed to load system settings');
      console.error('Error fetching settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      // TODO: Replace with actual API call
      // await adminService.updateSystemSettings(settings);
      console.log('Saving settings:', settings);
      setSuccess('Settings saved successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to save settings');
      console.error('Error saving settings:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleSettingChange = (section: keyof SystemSettings, field: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value,
      },
    }));
  };

  const handleMaintenanceMode = async () => {
    const newMode = !settings.general.maintenance_mode;
    try {
      // TODO: Implement maintenance mode toggle
      console.log('Toggle maintenance mode:', newMode);
      handleSettingChange('general', 'maintenance_mode', newMode);
    } catch (err) {
      console.error('Error toggling maintenance mode:', err);
    }
  };

  const handleCacheClear = async () => {
    try {
      // TODO: Implement cache clear
      console.log('Clear cache');
      setSuccess('Cache cleared successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to clear cache');
      console.error('Error clearing cache:', err);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading system settings..." />;
  }

  return (
    <>
      <PageHeader
        title="System Settings"
        breadcrumbs={[
          { label: 'Admin', path: '/admin' },
          { label: 'System Settings', path: '/admin/settings' },
        ]}
        action={
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleCacheClear}
            >
              Clear Cache
            </Button>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </Button>
          </Box>
        }
      />

      <Container maxWidth="lg">
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* General Settings */}
          <Grid item xs={12}>
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <SettingsIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">General Settings</Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Site Name"
                      value={settings.general.site_name}
                      onChange={(e) => handleSettingChange('general', 'site_name', e.target.value)}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Contact Email"
                      value={settings.general.contact_email}
                      onChange={(e) => handleSettingChange('general', 'contact_email', e.target.value)}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Site Description"
                      value={settings.general.site_description}
                      onChange={(e) => handleSettingChange('general', 'site_description', e.target.value)}
                      multiline
                      rows={2}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Support Phone"
                      value={settings.general.support_phone}
                      onChange={(e) => handleSettingChange('general', 'support_phone', e.target.value)}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth margin="normal">
                      <InputLabel>Timezone</InputLabel>
                      <Select
                        value={settings.general.timezone}
                        label="Timezone"
                        onChange={(e) => handleSettingChange('general', 'timezone', e.target.value)}
                      >
                        <MenuItem value="UTC">UTC</MenuItem>
                        <MenuItem value="America/New_York">Eastern Time</MenuItem>
                        <MenuItem value="America/Chicago">Central Time</MenuItem>
                        <MenuItem value="America/Denver">Mountain Time</MenuItem>
                        <MenuItem value="America/Los_Angeles">Pacific Time</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.general.maintenance_mode}
                          onChange={handleMaintenanceMode}
                          color="warning"
                        />
                      }
                      label="Maintenance Mode"
                    />
                    <Typography variant="caption" display="block" color="text.secondary">
                      When enabled, only administrators can access the site
                    </Typography>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Grid>

          {/* Security Settings */}
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <SecurityIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Security Settings</Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Session Timeout (minutes)"
                      value={settings.security.session_timeout}
                      onChange={(e) => handleSettingChange('security', 'session_timeout', parseInt(e.target.value))}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Max Login Attempts"
                      value={settings.security.max_login_attempts}
                      onChange={(e) => handleSettingChange('security', 'max_login_attempts', parseInt(e.target.value))}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Password Min Length"
                      value={settings.security.password_min_length}
                      onChange={(e) => handleSettingChange('security', 'password_min_length', parseInt(e.target.value))}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Max File Size (MB)"
                      value={settings.security.max_file_size}
                      onChange={(e) => handleSettingChange('security', 'max_file_size', parseInt(e.target.value))}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      Allowed File Types:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {settings.security.allowed_file_types.map((type) => (
                        <Chip key={type} label={type} size="small" />
                      ))}
                    </Box>
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.security.require_2fa}
                          onChange={(e) => handleSettingChange('security', 'require_2fa', e.target.checked)}
                        />
                      }
                      label="Require Two-Factor Authentication"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.security.enable_captcha}
                          onChange={(e) => handleSettingChange('security', 'enable_captcha', e.target.checked)}
                        />
                      }
                      label="Enable CAPTCHA on Login"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Grid>

          {/* Notification Settings */}
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <NotificationsIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Notification Settings</Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth margin="normal">
                      <InputLabel>Notification Frequency</InputLabel>
                      <Select
                        value={settings.notifications.notification_frequency}
                        label="Notification Frequency"
                        onChange={(e) => handleSettingChange('notifications', 'notification_frequency', e.target.value)}
                      >
                        <MenuItem value="immediate">Immediate</MenuItem>
                        <MenuItem value="hourly">Hourly</MenuItem>
                        <MenuItem value="daily">Daily</MenuItem>
                        <MenuItem value="weekly">Weekly</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.notifications.email_notifications}
                          onChange={(e) => handleSettingChange('notifications', 'email_notifications', e.target.checked)}
                        />
                      }
                      label="Email Notifications"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.notifications.sms_notifications}
                          onChange={(e) => handleSettingChange('notifications', 'sms_notifications', e.target.checked)}
                        />
                      }
                      label="SMS Notifications"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.notifications.push_notifications}
                          onChange={(e) => handleSettingChange('notifications', 'push_notifications', e.target.checked)}
                        />
                      }
                      label="Push Notifications"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.notifications.admin_notifications}
                          onChange={(e) => handleSettingChange('notifications', 'admin_notifications', e.target.checked)}
                        />
                      }
                      label="Admin Notifications"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Grid>

          {/* Performance Settings */}
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <StorageIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Performance Settings</Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Cache Duration (seconds)"
                      value={settings.performance.cache_duration}
                      onChange={(e) => handleSettingChange('performance', 'cache_duration', parseInt(e.target.value))}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Max Upload Size (MB)"
                      value={settings.performance.max_upload_size}
                      onChange={(e) => handleSettingChange('performance', 'max_upload_size', parseInt(e.target.value))}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.performance.cache_enabled}
                          onChange={(e) => handleSettingChange('performance', 'cache_enabled', e.target.checked)}
                        />
                      }
                      label="Enable Caching"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.performance.compression_enabled}
                          onChange={(e) => handleSettingChange('performance', 'compression_enabled', e.target.checked)}
                        />
                      }
                      label="Enable Compression"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.performance.cdn_enabled}
                          onChange={(e) => handleSettingChange('performance', 'cdn_enabled', e.target.checked)}
                        />
                      }
                      label="Enable CDN"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Grid>
        </Grid>
      </Container>
    </>
  );
};

export default SystemSettingsPage; 