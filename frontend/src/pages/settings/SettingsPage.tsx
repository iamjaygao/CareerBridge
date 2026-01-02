import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Button,
  Typography,
  Box,
  Switch,
  FormControlLabel,
  Slider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Grid,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Visibility as VisibilityIcon,
  Accessibility as AccessibilityIcon,
  Palette as PaletteIcon,
  Save as SaveIcon,
  Lock as LockIcon,
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '../../store';
import {
  setTheme,
  setLanguage,
  setNotificationSettings,
  setAccessibilitySettings,
  setPrivacySettings,
  setDisplaySettings,
} from '../../store/slices/settingsSlice';
import { useNotification } from '../../components/common/NotificationProvider';
import PageHeader from '../../components/common/PageHeader';
import ResponsiveContainer from '../../components/common/ResponsiveContainer';
import settingsService from '../../services/api/settingsService';
import PaymentIcon from '@mui/icons-material/Payment';

const SettingsPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const settings = useSelector((state: RootState) => state.settings);
  const user = useSelector((state: RootState) => state.auth.user);
  const { showSuccess } = useNotification();
  const [hasChanges, setHasChanges] = useState(false);
  const [privacyMsg, setPrivacyMsg] = useState<string | null>(null);
  const [kycStatus, setKycStatus] = useState<any | null>(null);
  const isStudent = user?.role === 'student';

  React.useEffect(() => {
    (async () => {
      try {
        const { OS_API } = await import('../../os/apiPaths');
        const res = await fetch(`${OS_API.HUMAN_LOOP}connect/status/`);
        if (res.ok) {
          const data = await res.json();
          setKycStatus(data);
        }
      } catch {}
    })();
  }, []);

  const handleThemeChange = (theme: 'light' | 'dark') => {
    dispatch(setTheme(theme));
    setHasChanges(true);
  };

  const handleLanguageChange = (language: string) => {
    dispatch(setLanguage(language));
    setHasChanges(true);
  };

  const handleNotificationChange = (setting: keyof typeof settings.notifications, value: boolean) => {
    dispatch(setNotificationSettings({ [setting]: value }));
    setHasChanges(true);
  };

  const handleAccessibilityChange = (setting: keyof typeof settings.accessibility, value: any) => {
    dispatch(setAccessibilitySettings({ [setting]: value }));
    setHasChanges(true);
  };

  const handlePrivacyChange = (setting: keyof typeof settings.privacy, value: boolean) => {
    dispatch(setPrivacySettings({ [setting]: value }));
    setHasChanges(true);
  };

  const handleDisplayChange = (setting: keyof typeof settings.display, value: boolean) => {
    dispatch(setDisplaySettings({ [setting]: value }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      await settingsService.updateUserSettings(settings);
      showSuccess('Settings saved successfully');
      setHasChanges(false);
    } catch (error) {
      showSuccess('Settings saved to local storage (offline mode)');
      settingsService.saveToLocalStorage(settings);
      setHasChanges(false);
    }
  };

  return (
    <ResponsiveContainer>
      <PageHeader
        title="Settings"
        breadcrumbs={[{ label: 'Settings', path: '/settings' }]}
        action={
          hasChanges && (
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
            >
              Save Changes
            </Button>
          )
        }
      />

      <Grid container spacing={3}>
        {/* Appearance Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PaletteIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Appearance</Typography>
              </Box>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Theme</InputLabel>
                <Select
                  value={settings.theme}
                  onChange={(e) => handleThemeChange(e.target.value as 'light' | 'dark')}
                  label="Theme"
                >
                  <MenuItem value="light">Light</MenuItem>
                  <MenuItem value="dark">Dark</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth>
                <InputLabel>Language</InputLabel>
                <Select
                  value={settings.language}
                  onChange={(e) => handleLanguageChange(e.target.value)}
                  label="Language"
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="zh">中文</MenuItem>
                  <MenuItem value="es">Español</MenuItem>
                </Select>
              </FormControl>
            </CardContent>
          </Card>
        </Grid>

        {/* Notification Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <NotificationsIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Notifications</Typography>
              </Box>

              <List>
                <ListItem>
                  <ListItemText
                    primary="Email Notifications"
                    secondary="Receive notifications via email"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.notifications.email}
                      onChange={(e) => handleNotificationChange('email', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Push Notifications"
                    secondary="Receive push notifications in browser"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.notifications.push}
                      onChange={(e) => handleNotificationChange('push', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Desktop Notifications"
                    secondary="Show desktop notifications"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.notifications.desktop}
                      onChange={(e) => handleNotificationChange('desktop', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Accessibility Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AccessibilityIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Accessibility</Typography>
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography gutterBottom>Font Size</Typography>
                <Slider
                  value={settings.accessibility.fontSize}
                  onChange={(e, value) => handleAccessibilityChange('fontSize', value)}
                  min={12}
                  max={24}
                  step={1}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Contrast</InputLabel>
                <Select
                  value={settings.accessibility.contrast}
                  onChange={(e) => handleAccessibilityChange('contrast', e.target.value)}
                  label="Contrast"
                >
                  <MenuItem value="normal">Normal</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                </Select>
              </FormControl>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.accessibility.reducedMotion}
                    onChange={(e) => handleAccessibilityChange('reducedMotion', e.target.checked)}
                  />
                }
                label="Reduce Motion"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Privacy Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <VisibilityIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Privacy</Typography>
              </Box>

              <List>
                <ListItem>
                  <ListItemText
                    primary="Share Profile"
                    secondary="Allow others to view your profile"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.privacy.shareProfile}
                      onChange={(e) => handlePrivacyChange('shareProfile', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Show Online Status"
                    secondary="Show when you're online"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.privacy.showOnlineStatus}
                      onChange={(e) => handlePrivacyChange('showOnlineStatus', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Privacy & Data Actions */}
        {isStudent && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <LockIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Privacy & Data</Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Button variant="outlined" onClick={() => navigate('/student/settings/consent')}>
                    Manage Consents
                  </Button>
                  <Button variant="outlined" onClick={async () => {
                    setPrivacyMsg(null);
                    const { OS_API } = await import('../../os/apiPaths');
                    const res = await fetch(`${OS_API.ATS_SIGNALS}data/deletion/request/`, { method: 'POST' });
                    const data = await res.json();
                    if (!res.ok) return setPrivacyMsg(data.error || 'Failed to request deletion');
                    setPrivacyMsg(`Deletion requested. Token: ${data.token}`);
                  }}>Request Deletion</Button>
                  <Button variant="outlined" onClick={async () => {
                    setPrivacyMsg(null);
                    const { OS_API } = await import('../../os/apiPaths');
                    const res = await fetch(`${OS_API.ATS_SIGNALS}privacy/export/`, { method: 'POST' });
                    const data = await res.json();
                    if (!res.ok) return setPrivacyMsg(data.error || 'Failed to request export');
                    setPrivacyMsg('Export job started. Check status shortly.');
                  }}>Request Export</Button>
                  <Button variant="contained" onClick={async () => {
                    setPrivacyMsg(null);
                    const { OS_API } = await import('../../os/apiPaths');
                    const res = await fetch(`${OS_API.ATS_SIGNALS}privacy/export/status/`);
                    const data = await res.json();
                    if (!res.ok) return setPrivacyMsg('Failed to fetch export status');
                    if (data.status === 'completed' && data.download_url) {
                      setPrivacyMsg('Export ready. Downloading...');
                      window.location.href = data.download_url;
                    } else {
                      setPrivacyMsg(`Export status: ${data.status}`);
                    }
                  }}>Check Export Status</Button>
                </Box>
                {privacyMsg && <Alert severity="info" sx={{ mt: 2 }}>{privacyMsg}</Alert>}
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Mentor Connect Onboarding */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PaymentIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Mentor Payments (Stripe Connect)</Typography>
              </Box>
              {kycStatus && (
                <Box sx={{ mb: 2 }}>
                  {(!kycStatus.payouts_enabled || !kycStatus.charges_enabled) ? (
                    <Alert severity="warning">Your Stripe account is not fully enabled. Please complete onboarding. {kycStatus.kyc_disabled_reason && `(Reason: ${kycStatus.kyc_disabled_reason})`}</Alert>
                  ) : (
                    <Alert severity="success">Stripe Connect is fully enabled for payouts and charges.</Alert>
                  )}
                </Box>
              )}
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button variant="outlined" onClick={async () => {
                  const { OS_API } = await import('../../os/apiPaths');
                  const res = await fetch(`${OS_API.HUMAN_LOOP}connect/create-account/`, { method: 'POST' });
                  const data = await res.json();
                  if (!res.ok) return alert(data.error || 'Failed to create account');
                  alert(`Account ID: ${data.account_id}`);
                }}>Create/Fetch Account</Button>
                <Button variant="contained" onClick={async () => {
                  const { OS_API } = await import('../../os/apiPaths');
                  const params = new URLSearchParams({
                    return_url: window.location.origin + '/settings',
                    refresh_url: window.location.origin + '/settings'
                  });
                  const res = await fetch(`${OS_API.HUMAN_LOOP}connect/account-link/?${params}`, { method: 'POST' });
                  const data = await res.json();
                  if (!res.ok) return alert(data.error || 'Failed to create account link');
                  window.location.href = data.url;
                }}>Start Onboarding</Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Display Settings */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Display Options
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.display.sidebarCollapsed}
                        onChange={(e) => handleDisplayChange('sidebarCollapsed', e.target.checked)}
                      />
                    }
                    label="Collapsed Sidebar"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.display.denseMode}
                        onChange={(e) => handleDisplayChange('denseMode', e.target.checked)}
                      />
                    }
                    label="Dense Mode"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.display.listView}
                        onChange={(e) => handleDisplayChange('listView', e.target.checked)}
                      />
                    }
                    label="List View"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </ResponsiveContainer>
  );
};

export default SettingsPage; 
