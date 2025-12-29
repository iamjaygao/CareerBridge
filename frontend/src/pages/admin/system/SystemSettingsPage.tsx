import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
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
  Card,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Campaign as CampaignIcon,
  Palette as PaletteIcon,
  Public as PublicIcon,
  Key as KeyIcon,
  Email as EmailIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';

import LoadingSpinner from '../../../components/common/LoadingSpinner';
import adminService from '../../../services/api/adminService';

interface SystemSettings {
  platform_name: string;
  company_name: string;
  support_email: string;
  support_phone: string;
  office_address: string;
  website_url: string;
  contact_title: string;
  contact_description: string;
  announcement_enabled: boolean;
  announcement_text: string;
  announcement_type: 'info' | 'warning' | 'error' | 'success';
  primary_color: string;
  accent_color: string;
  logo_url: string;
  favicon_url: string;
  theme: 'light' | 'dark' | 'auto';
  linkedin_url: string;
  twitter_url: string;
  instagram_url: string;
  youtube_url: string;
  facebook_url: string;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_from_name: string;
  template_footer_text: string;
}

const emptySettings: SystemSettings = {
  platform_name: '',
  company_name: '',
  support_email: '',
  support_phone: '',
  office_address: '',
  website_url: '',
  contact_title: '',
  contact_description: '',
  announcement_enabled: false,
  announcement_text: '',
  announcement_type: 'info',
  primary_color: '#2374e1',
  accent_color: '#64748b',
  logo_url: '',
  favicon_url: '',
  theme: 'light',
  linkedin_url: '',
  twitter_url: '',
  instagram_url: '',
  youtube_url: '',
  facebook_url: '',
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_from_name: '',
  template_footer_text: '',
};

const emptyApiKeys = {
  openai_api_key: '',
  stripe_secret_key: '',
  email_api_key: '',
  google_oauth_key: '',
};

const SystemSettingsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [settings, setSettings] = useState<SystemSettings>(emptySettings);
  const [apiKeys, setApiKeys] = useState(emptyApiKeys);
  const [maskedKeys, setMaskedKeys] = useState(emptyApiKeys);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const data = await adminService.getSystemSettings();
      setSettings({ ...emptySettings, ...data });
      setMaskedKeys({
        openai_api_key: data.openai_api_key || '',
        stripe_secret_key: data.stripe_secret_key || '',
        email_api_key: data.email_api_key || '',
        google_oauth_key: data.google_oauth_key || '',
      });
      setApiKeys(emptyApiKeys);
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
      const payload: Record<string, any> = { ...settings };

      Object.entries(apiKeys).forEach(([key, value]) => {
        if (value && value.trim()) {
          payload[key] = value.trim();
        }
      });

      const updated = await adminService.updateSystemSettings(payload);
      setSettings({ ...emptySettings, ...updated });
      setMaskedKeys({
        openai_api_key: updated.openai_api_key || '',
        stripe_secret_key: updated.stripe_secret_key || '',
        email_api_key: updated.email_api_key || '',
        google_oauth_key: updated.google_oauth_key || '',
      });
      setApiKeys(emptyApiKeys);
      setSuccess('Settings saved successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to save settings');
      console.error('Error saving settings:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleCacheClear = async () => {
    try {
      await adminService.clearCache();
      setSuccess('Cache cleared successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to clear cache');
      console.error('Error clearing cache:', err);
    }
  };

  const handleSettingChange = (field: keyof SystemSettings, value: any) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return <LoadingSpinner message="Loading system settings..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          System Settings
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Manage platform-wide configuration and preferences
        </Typography>
      </Box>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', gap: 2, mb: 4, justifyContent: 'flex-end' }}>
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
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
            },
          }}
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </Box>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Settings Sections */}
      <Grid container spacing={3}>
        {/* General Settings */}
        <Grid item xs={12}>
          <Card>
            <Accordion defaultExpanded>
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{ bgcolor: 'grey.50', '&:hover': { bgcolor: 'grey.100' } }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <SettingsIcon sx={{ mr: 2, color: 'primary.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Platform Settings
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3} sx={{ pt: 2 }}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Platform Name"
                      value={settings.platform_name}
                      onChange={(e) => handleSettingChange('platform_name', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Company Name"
                      value={settings.company_name}
                      onChange={(e) => handleSettingChange('company_name', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Support Email"
                      type="email"
                      value={settings.support_email}
                      onChange={(e) => handleSettingChange('support_email', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Support Phone"
                      value={settings.support_phone}
                      onChange={(e) => handleSettingChange('support_phone', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Office Address"
                      value={settings.office_address}
                      onChange={(e) => handleSettingChange('office_address', e.target.value)}
                      multiline
                      rows={2}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Website URL"
                      value={settings.website_url}
                      onChange={(e) => handleSettingChange('website_url', e.target.value)}
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Card>
        </Grid>

        {/* Announcement Settings */}
        <Grid item xs={12}>
          <Card>
            <Accordion>
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{ bgcolor: 'grey.50', '&:hover': { bgcolor: 'grey.100' } }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <CampaignIcon sx={{ mr: 2, color: 'primary.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Announcement Settings
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3} sx={{ pt: 2 }}>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.announcement_enabled}
                          onChange={(e) => handleSettingChange('announcement_enabled', e.target.checked)}
                        />
                      }
                      label="Enable Announcement Banner"
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth>
                      <InputLabel>Announcement Type</InputLabel>
                      <Select
                        value={settings.announcement_type}
                        label="Announcement Type"
                        onChange={(e) => handleSettingChange('announcement_type', e.target.value)}
                      >
                        <MenuItem value="info">Info</MenuItem>
                        <MenuItem value="warning">Warning</MenuItem>
                        <MenuItem value="error">Error</MenuItem>
                        <MenuItem value="success">Success</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Announcement Text"
                      value={settings.announcement_text}
                      onChange={(e) => handleSettingChange('announcement_text', e.target.value)}
                      multiline
                      rows={2}
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Card>
        </Grid>

        {/* Appearance Settings */}
        <Grid item xs={12}>
          <Card>
            <Accordion>
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{ bgcolor: 'grey.50', '&:hover': { bgcolor: 'grey.100' } }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <PaletteIcon sx={{ mr: 2, color: 'primary.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Appearance
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3} sx={{ pt: 2 }}>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Primary Color"
                      value={settings.primary_color}
                      onChange={(e) => handleSettingChange('primary_color', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Accent Color"
                      value={settings.accent_color}
                      onChange={(e) => handleSettingChange('accent_color', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth>
                      <InputLabel>Theme</InputLabel>
                      <Select
                        value={settings.theme}
                        label="Theme"
                        onChange={(e) => handleSettingChange('theme', e.target.value)}
                      >
                        <MenuItem value="light">Light</MenuItem>
                        <MenuItem value="dark">Dark</MenuItem>
                        <MenuItem value="auto">Auto</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Logo URL"
                      value={settings.logo_url}
                      onChange={(e) => handleSettingChange('logo_url', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Favicon URL"
                      value={settings.favicon_url}
                      onChange={(e) => handleSettingChange('favicon_url', e.target.value)}
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Card>
        </Grid>

        {/* Contact Page */}
        <Grid item xs={12}>
          <Card>
            <Accordion>
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{ bgcolor: 'grey.50', '&:hover': { bgcolor: 'grey.100' } }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <PublicIcon sx={{ mr: 2, color: 'primary.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Contact Page
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3} sx={{ pt: 2 }}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Contact Title"
                      value={settings.contact_title}
                      onChange={(e) => handleSettingChange('contact_title', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Contact Description"
                      value={settings.contact_description}
                      onChange={(e) => handleSettingChange('contact_description', e.target.value)}
                      multiline
                      rows={2}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="LinkedIn URL"
                      value={settings.linkedin_url}
                      onChange={(e) => handleSettingChange('linkedin_url', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Twitter URL"
                      value={settings.twitter_url}
                      onChange={(e) => handleSettingChange('twitter_url', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Instagram URL"
                      value={settings.instagram_url}
                      onChange={(e) => handleSettingChange('instagram_url', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="YouTube URL"
                      value={settings.youtube_url}
                      onChange={(e) => handleSettingChange('youtube_url', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Facebook URL"
                      value={settings.facebook_url}
                      onChange={(e) => handleSettingChange('facebook_url', e.target.value)}
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Card>
        </Grid>

        {/* API Keys */}
        <Grid item xs={12}>
          <Card>
            <Accordion>
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{ bgcolor: 'grey.50', '&:hover': { bgcolor: 'grey.100' } }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <KeyIcon sx={{ mr: 2, color: 'primary.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    API Keys
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3} sx={{ pt: 2 }}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="OpenAI API Key"
                      type="password"
                      value={apiKeys.openai_api_key}
                      onChange={(e) => setApiKeys(prev => ({ ...prev, openai_api_key: e.target.value }))}
                      helperText={maskedKeys.openai_api_key ? `Current: ${maskedKeys.openai_api_key}` : 'Not set'}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Stripe Secret Key"
                      type="password"
                      value={apiKeys.stripe_secret_key}
                      onChange={(e) => setApiKeys(prev => ({ ...prev, stripe_secret_key: e.target.value }))}
                      helperText={maskedKeys.stripe_secret_key ? `Current: ${maskedKeys.stripe_secret_key}` : 'Not set'}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Email API Key"
                      type="password"
                      value={apiKeys.email_api_key}
                      onChange={(e) => setApiKeys(prev => ({ ...prev, email_api_key: e.target.value }))}
                      helperText={maskedKeys.email_api_key ? `Current: ${maskedKeys.email_api_key}` : 'Not set'}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Google OAuth Key"
                      type="password"
                      value={apiKeys.google_oauth_key}
                      onChange={(e) => setApiKeys(prev => ({ ...prev, google_oauth_key: e.target.value }))}
                      helperText={maskedKeys.google_oauth_key ? `Current: ${maskedKeys.google_oauth_key}` : 'Not set'}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="caption" color="text.secondary">
                      Leave fields blank to keep existing keys unchanged.
                    </Typography>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Card>
        </Grid>

        {/* Email Settings */}
        <Grid item xs={12}>
          <Card>
            <Accordion>
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{ bgcolor: 'grey.50', '&:hover': { bgcolor: 'grey.100' } }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <EmailIcon sx={{ mr: 2, color: 'primary.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Email Configuration
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3} sx={{ pt: 2 }}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="SMTP Host"
                      value={settings.smtp_host}
                      onChange={(e) => handleSettingChange('smtp_host', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <TextField
                      fullWidth
                      type="number"
                      label="SMTP Port"
                      value={settings.smtp_port}
                      onChange={(e) => handleSettingChange('smtp_port', Number(e.target.value))}
                    />
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <TextField
                      fullWidth
                      label="SMTP Username"
                      value={settings.smtp_username}
                      onChange={(e) => handleSettingChange('smtp_username', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="From Name"
                      value={settings.smtp_from_name}
                      onChange={(e) => handleSettingChange('smtp_from_name', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Email Template Footer"
                      value={settings.template_footer_text}
                      onChange={(e) => handleSettingChange('template_footer_text', e.target.value)}
                      multiline
                      rows={2}
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SystemSettingsPage;
