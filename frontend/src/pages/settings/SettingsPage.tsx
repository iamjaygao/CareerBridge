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
} from '@mui/material';
import { Grid } from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Visibility as VisibilityIcon,
  Accessibility as AccessibilityIcon,
  Palette as PaletteIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
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

const SettingsPage: React.FC = () => {
  const dispatch = useDispatch();
  const settings = useSelector((state: RootState) => state.settings);
  const { showSuccess } = useNotification();
  const [hasChanges, setHasChanges] = useState(false);

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