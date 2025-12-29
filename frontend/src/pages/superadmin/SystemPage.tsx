import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  Switch,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Snackbar,
  IconButton,
  InputAdornment,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CloudDone as CloudDoneIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  TrendingUp as TrendingUpIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Upload as UploadIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { useRole } from '../../contexts/RoleContext';
import adminService from '../../services/api/adminService';
import { SystemHealth, SystemSettings } from '../../types';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { useNotification } from '../../components/common/NotificationProvider';

const SystemPage: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const { isSuperAdmin } = useRole();
  const { showNotification } = useNotification();
  
  // Loading states
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  
  // Error states
  const [error, setError] = useState<string | null>(null);
  
  // Data states
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [systemSettings, setSystemSettings] = useState<SystemSettings | null>(null);
  const [errorLogs, setErrorLogs] = useState<string[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditFilters, setAuditFilters] = useState({
    admin_user: '',
    action_type: '',
    date_from: '',
    date_to: '',
  });
  
  // Dialog states
  const [errorLogsOpen, setErrorLogsOpen] = useState(false);
  
  // Form states for settings
  const [settingsForm, setSettingsForm] = useState<Partial<SystemSettings>>({});
  
  // Password visibility states
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({});
  
  // Accordion expanded states
  const [expandedAccordion, setExpandedAccordion] = useState<string | false>(false);
  
  const handleAccordionChange = (panel: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedAccordion(isExpanded ? panel : false);
  };

  useEffect(() => {
    if (isSuperAdmin) {
      fetchSystemData();
    }
  }, [isSuperAdmin]);

  const fetchSystemData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [healthData, settingsData, actionsData] = await Promise.all([
        adminService.getSystemHealth(),
        adminService.getSystemSettings(),
        adminService.getAdminActions({ page_size: 10 }),
      ]);
      
      setSystemHealth(healthData);
      setSystemSettings(settingsData);
      setSettingsForm(settingsData);
      setAuditLogs(Array.isArray(actionsData) ? actionsData : (actionsData?.results || []));
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail 
        || err?.response?.data?.error
        || err?.message 
        || 'Failed to load system data';
      setError(errorMessage);
      console.error('Failed to fetch system data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      setAuditLoading(true);
      const params: any = { page_size: 20 };
      if (auditFilters.admin_user) params.admin_user = auditFilters.admin_user;
      if (auditFilters.action_type) params.action_type = auditFilters.action_type;
      if (auditFilters.date_from) params.date_from = auditFilters.date_from;
      if (auditFilters.date_to) params.date_to = auditFilters.date_to;
      const data = await adminService.getAdminActions(params);
      setAuditLogs(Array.isArray(data) ? data : (data?.results || []));
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail 
        || err?.response?.data?.error
        || err?.message 
        || 'Failed to load audit logs';
      showNotification(errorMessage, 'error');
    } finally {
      setAuditLoading(false);
    }
  };

  const handleSaveSettings = async (section: string) => {
    try {
      setSaving(section);
      const dataToSave: any = {};
      
      // Extract fields for the section
      if (section === 'platform') {
        Object.assign(dataToSave, {
          platform_name: settingsForm.platform_name,
          company_name: settingsForm.company_name,
          support_email: settingsForm.support_email,
          support_phone: settingsForm.support_phone,
          office_address: settingsForm.office_address,
          website_url: settingsForm.website_url,
        });
      } else if (section === 'announcement') {
        Object.assign(dataToSave, {
          announcement_enabled: settingsForm.announcement_enabled,
          announcement_title: settingsForm.announcement_title,
          announcement_text: settingsForm.announcement_message || settingsForm.announcement_text,
          announcement_type: settingsForm.announcement_type,
        });
      } else if (section === 'appearance') {
        Object.assign(dataToSave, {
          primary_color: settingsForm.primary_color,
          accent_color: settingsForm.accent_color || settingsForm.secondary_color,
          logo_url: settingsForm.logo_url,
          favicon_url: settingsForm.favicon_url,
          theme: settingsForm.theme,
          enable_dark_mode: settingsForm.enable_dark_mode,
        });
      } else if (section === 'contact') {
        Object.assign(dataToSave, {
          contact_title: settingsForm.contact_title,
          contact_description: settingsForm.contact_description,
        });
      } else if (section === 'social') {
        Object.assign(dataToSave, {
          contact_email: settingsForm.contact_email,
          contact_phone: settingsForm.contact_phone,
          linkedin_url: settingsForm.linkedin_url,
          twitter_url: settingsForm.twitter_url,
          instagram_url: settingsForm.instagram_url,
          youtube_url: settingsForm.youtube_url,
          facebook_url: settingsForm.facebook_url,
        });
      } else if (section === 'api-keys') {
        Object.assign(dataToSave, {
          openai_api_key: settingsForm.openai_api_key,
          stripe_secret_key: settingsForm.stripe_api_key || settingsForm.stripe_secret_key,
          email_api_key: settingsForm.email_api_key,
          smtp_api_key: settingsForm.smtp_api_key,
        });
      } else if (section === 'email') {
        Object.assign(dataToSave, {
          smtp_host: settingsForm.smtp_host,
          smtp_port: settingsForm.smtp_port,
          smtp_username: settingsForm.smtp_username,
          smtp_password: settingsForm.smtp_password,
          smtp_from_name: settingsForm.smtp_from_name,
          template_footer_text: settingsForm.template_footer_text,
          enable_tls: settingsForm.enable_tls,
        });
      }
      
      const updated = await adminService.updateSystemSettings(dataToSave);
      setSystemSettings(updated);
      setSettingsForm(updated);
      showNotification('Settings saved successfully', 'success');
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail 
        || err?.response?.data?.error
        || err?.message 
        || 'Failed to save settings';
      showNotification(errorMessage, 'error');
    } finally {
      setSaving(null);
    }
  };

  const handleSystemAction = async (action: string) => {
    try {
      setActionLoading(action);
      
      let result;
      if (action === 'clear-cache') {
        result = await adminService.clearCache();
      } else if (action === 'error-logs') {
        const logs = await adminService.getErrorLogs();
        setErrorLogs(logs.logs || []);
        setErrorLogsOpen(true);
        setActionLoading(null);
        return;
      } else if (action === 'reset-rate-limits') {
        result = await adminService.resetRateLimits();
      } else if (action === 'rebuild-index') {
        result = await adminService.rebuildSearchIndex();
      }
      
      showNotification(result?.message || `${action} completed successfully`, 'success');
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail 
        || err?.response?.data?.error
        || err?.message 
        || `Failed to execute ${action}`;
      showNotification(errorMessage, 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const getHealthColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'online':
      case 'connected':
        return '#059669'; // Green
      case 'degraded':
      case 'warning':
        return '#f59e0b'; // Amber
      case 'error':
      case 'offline':
      case 'disconnected':
        return '#dc2626'; // Red
      default:
        return '#6b7280'; // Gray
    }
  };

  const getHealthIcon = (status: string) => {
    const color = getHealthColor(status);
    if (color === '#059669') return <CheckCircleIcon sx={{ color }} />;
    if (color === '#f59e0b') return <WarningIcon sx={{ color }} />;
    return <ErrorIcon sx={{ color }} />;
  };

  if (!isSuperAdmin) {
    return null;
  }

  if (loading) {
    return <LoadingSpinner message="Loading system console..." />;
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Page Header */}
      <Box sx={{ mb: 6 }}>
        <Typography 
          variant="h4" 
          component="h1" 
          gutterBottom 
          sx={{ fontWeight: 700, mb: 1 }}
        >
          System Control Center
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitor system health, configure platform settings, and manage system operations
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* SECTION 1: System Health */}
      <Paper 
        sx={{ 
          p: 3, 
          mb: 3,
          borderRadius: 2,
          boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
        }}
      >
        <Typography 
          variant="h5" 
          gutterBottom 
          sx={{ 
            fontWeight: 600, 
            mb: 3,
            textAlign: 'left',
          }}
        >
          System Health
        </Typography>
        <Grid container spacing={3}>
          {/* System Health */}
          <Grid item xs={12} sm={6} md={4} lg={2.4}>
            <Card 
              sx={{ 
                height: '100%',
                borderRadius: 2,
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <Box sx={{ mb: 2 }}>
                  {getHealthIcon(systemHealth?.system_health || 'unknown')}
                </Box>
                <Typography 
                  variant="h4" 
                  sx={{ 
                    color: getHealthColor(systemHealth?.system_health || 'unknown'),
                    fontWeight: 600,
                    mb: 1,
                  }}
                >
                  {systemHealth?.system_health || 'Unknown'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  System Health
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Backend Status */}
          <Grid item xs={12} sm={6} md={4} lg={2.4}>
            <Card 
              sx={{ 
                height: '100%',
                borderRadius: 2,
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <Box sx={{ mb: 2 }}>
                  <CloudDoneIcon sx={{ color: getHealthColor(systemHealth?.backend_status || 'unknown'), fontSize: 40 }} />
                </Box>
                <Typography 
                  variant="h4" 
                  sx={{ 
                    color: getHealthColor(systemHealth?.backend_status || 'unknown'),
                    fontWeight: 600,
                    mb: 1,
                  }}
                >
                  {systemHealth?.backend_status || 'Unknown'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Backend Status
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Database Status */}
          <Grid item xs={12} sm={6} md={4} lg={2.4}>
            <Card 
              sx={{ 
                height: '100%',
                borderRadius: 2,
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <Box sx={{ mb: 2 }}>
                  <StorageIcon sx={{ color: getHealthColor(systemHealth?.database_status || 'unknown'), fontSize: 40 }} />
                </Box>
                <Typography 
                  variant="h4" 
                  sx={{ 
                    color: getHealthColor(systemHealth?.database_status || 'unknown'),
                    fontWeight: 600,
                    mb: 1,
                  }}
                >
                  {systemHealth?.database_status || 'Unknown'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Database Status
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Cache Status */}
          <Grid item xs={12} sm={6} md={4} lg={2.4}>
            <Card 
              sx={{ 
                height: '100%',
                borderRadius: 2,
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <Box sx={{ mb: 2 }}>
                  <StorageIcon sx={{ color: getHealthColor(systemHealth?.cache_status || 'unknown'), fontSize: 40 }} />
                </Box>
                <Typography 
                  variant="h4" 
                  sx={{ 
                    color: getHealthColor(systemHealth?.cache_status || 'unknown'),
                    fontWeight: 600,
                    mb: 1,
                  }}
                >
                  {systemHealth?.cache_status || 'Unknown'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Cache Status
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          {/* API Response Time */}
          <Grid item xs={12} sm={6} md={4} lg={2.4}>
            <Card 
              sx={{ 
                height: '100%',
                borderRadius: 2,
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <Box sx={{ mb: 2 }}>
                  <SpeedIcon sx={{ color: '#2563eb', fontSize: 40 }} />
                </Box>
                <Typography 
                  variant="h4" 
                  sx={{ 
                    color: '#2563eb',
                    fontWeight: 600,
                    mb: 1,
                  }}
                >
                  {systemHealth?.api_response_time !== undefined && systemHealth?.api_response_time !== null 
                    ? `${systemHealth.api_response_time.toFixed(2)}ms` 
                    : 'Unavailable'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  API Response Time
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* SECTION 2: System Configuration */}
      <Paper 
        sx={{ 
          p: 3, 
          mb: 3,
          borderRadius: 2,
          boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
        }}
      >
        <Typography 
          variant="h5" 
          gutterBottom 
          sx={{ 
            fontWeight: 600, 
            mb: 3,
            textAlign: 'left',
          }}
        >
          System Configuration
        </Typography>
        
        {/* Platform Settings */}
        <Accordion 
          expanded={expandedAccordion === 'platform'}
          onChange={handleAccordionChange('platform')}
          sx={{ 
            mb: 2,
            borderRadius: 1,
            '&:before': { display: 'none' },
            boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
            transition: 'all 0.3s ease-in-out',
          }}
        >
          <AccordionSummary 
            expandIcon={<ExpandMoreIcon />}
            sx={{ px: 2, py: 1.5 }}
          >
            <Typography variant="h6" sx={{ fontWeight: 500 }}>
              Platform Settings
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ px: 3, pb: 3 }}>
            <Grid container spacing={3}>
              {/* First row: 2-column grid for first 4 fields */}
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Platform Name"
                  value={settingsForm.platform_name || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, platform_name: e.target.value })}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Company Name"
                  value={settingsForm.company_name || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, company_name: e.target.value })}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Website URL"
                  type="url"
                  value={settingsForm.website_url || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, website_url: e.target.value })}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Support Email"
                  type="email"
                  value={settingsForm.support_email || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, support_email: e.target.value })}
                  margin="normal"
                />
              </Grid>
              {/* Office Address: full row */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Office Address"
                  multiline
                  rows={3}
                  value={settingsForm.office_address || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, office_address: e.target.value })}
                  margin="normal"
                />
              </Grid>
              {/* Support Phone: full row */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Support Phone"
                  value={settingsForm.support_phone || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, support_phone: e.target.value })}
                  margin="normal"
                />
              </Grid>
            </Grid>
            {/* Save button: always visible when accordion is expanded, aligned to right */}
            {expandedAccordion === 'platform' && (
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  startIcon={saving === 'platform' ? <CircularProgress size={20} /> : <SaveIcon />}
                  onClick={() => handleSaveSettings('platform')}
                  disabled={saving === 'platform'}
                >
                  Save Platform Settings
                </Button>
              </Box>
            )}
          </AccordionDetails>
        </Accordion>

        {/* Announcement Settings */}
        <Accordion 
          expanded={expandedAccordion === 'announcement'}
          onChange={handleAccordionChange('announcement')}
          sx={{ 
            mb: 2,
            borderRadius: 1,
            '&:before': { display: 'none' },
            boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
            transition: 'all 0.3s ease-in-out',
          }}
        >
          <AccordionSummary 
            expandIcon={<ExpandMoreIcon />}
            sx={{ px: 2, py: 1.5 }}
          >
            <Typography variant="h6" sx={{ fontWeight: 500 }}>
              Announcement Settings
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ px: 3, pb: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Switch
                    checked={settingsForm.announcement_enabled || false}
                    onChange={(e) => setSettingsForm({ ...settingsForm, announcement_enabled: e.target.checked })}
                  />
                  <Typography>Enable System Announcement</Typography>
                </Box>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Announcement Title"
                  value={settingsForm.announcement_title || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, announcement_title: e.target.value })}
                  margin="normal"
                  disabled={!settingsForm.announcement_enabled}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Announcement Message"
                  multiline
                  rows={4}
                  value={settingsForm.announcement_message || settingsForm.announcement_text || ''}
                  onChange={(e) => setSettingsForm({ 
                    ...settingsForm, 
                    announcement_message: e.target.value,
                    announcement_text: e.target.value,
                  })}
                  margin="normal"
                  disabled={!settingsForm.announcement_enabled}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel>Announcement Type</InputLabel>
                  <Select
                    value={settingsForm.announcement_type || 'info'}
                    label="Announcement Type"
                    onChange={(e) => setSettingsForm({ ...settingsForm, announcement_type: e.target.value as any })}
                    disabled={!settingsForm.announcement_enabled}
                  >
                    <MenuItem value="info">Info</MenuItem>
                    <MenuItem value="warning">Warning</MenuItem>
                    <MenuItem value="error">Error</MenuItem>
                    <MenuItem value="success">Success</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
            {expandedAccordion === 'announcement' && (
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  startIcon={saving === 'announcement' ? <CircularProgress size={20} /> : <SaveIcon />}
                  onClick={() => handleSaveSettings('announcement')}
                  disabled={saving === 'announcement'}
                >
                  Save Announcement Settings
                </Button>
              </Box>
            )}
          </AccordionDetails>
        </Accordion>

        {/* Branding / Appearance Settings */}
        <Accordion 
          expanded={expandedAccordion === 'appearance'}
          onChange={handleAccordionChange('appearance')}
          sx={{ 
            mb: 2,
            borderRadius: 1,
            '&:before': { display: 'none' },
            boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
            transition: 'all 0.3s ease-in-out',
          }}
        >
          <AccordionSummary 
            expandIcon={<ExpandMoreIcon />}
            sx={{ px: 2, py: 1.5 }}
          >
            <Typography variant="h6" sx={{ fontWeight: 500 }}>
              Branding / Appearance Settings
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ px: 3, pb: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <TextField
                    label="Primary Color"
                    type="color"
                    value={settingsForm.primary_color || '#2374e1'}
                    onChange={(e) => setSettingsForm({ ...settingsForm, primary_color: e.target.value })}
                    margin="normal"
                    InputLabelProps={{ shrink: true }}
                    sx={{ width: 100 }}
                  />
                  <TextField
                    fullWidth
                    label="Primary Color (Hex)"
                    value={settingsForm.primary_color || '#2374e1'}
                    onChange={(e) => setSettingsForm({ ...settingsForm, primary_color: e.target.value })}
                    margin="normal"
                  />
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <TextField
                    label="Accent Color"
                    type="color"
                    value={settingsForm.accent_color || settingsForm.secondary_color || '#64748b'}
                    onChange={(e) => setSettingsForm({ 
                      ...settingsForm, 
                      accent_color: e.target.value,
                      secondary_color: e.target.value,
                    })}
                    margin="normal"
                    InputLabelProps={{ shrink: true }}
                    sx={{ width: 100 }}
                  />
                  <TextField
                    fullWidth
                    label="Accent Color (Hex)"
                    value={settingsForm.accent_color || settingsForm.secondary_color || '#64748b'}
                    onChange={(e) => setSettingsForm({ 
                      ...settingsForm, 
                      accent_color: e.target.value,
                      secondary_color: e.target.value,
                    })}
                    margin="normal"
                  />
                </Box>
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Switch
                    checked={settingsForm.enable_dark_mode || false}
                    onChange={(e) => setSettingsForm({ ...settingsForm, enable_dark_mode: e.target.checked })}
                  />
                  <Typography>Enable Dark Mode</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Logo URL"
                  type="url"
                  value={settingsForm.logo_url || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, logo_url: e.target.value })}
                  margin="normal"
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton size="small" edge="end">
                          <UploadIcon />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Favicon URL"
                  type="url"
                  value={settingsForm.favicon_url || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, favicon_url: e.target.value })}
                  margin="normal"
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton size="small" edge="end">
                          <UploadIcon />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
            </Grid>
            {expandedAccordion === 'appearance' && (
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  startIcon={saving === 'appearance' ? <CircularProgress size={20} /> : <SaveIcon />}
                  onClick={() => handleSaveSettings('appearance')}
                  disabled={saving === 'appearance'}
                >
                  Save Appearance Settings
                </Button>
              </Box>
            )}
          </AccordionDetails>
        </Accordion>

        {/* Contact Settings */}
        <Accordion 
          expanded={expandedAccordion === 'contact'}
          onChange={handleAccordionChange('contact')}
          sx={{ 
            mb: 2,
            borderRadius: 1,
            '&:before': { display: 'none' },
            boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
            transition: 'all 0.3s ease-in-out',
          }}
        >
          <AccordionSummary 
            expandIcon={<ExpandMoreIcon />}
            sx={{ px: 2, py: 1.5 }}
          >
            <Typography variant="h6" sx={{ fontWeight: 500 }}>
              Contact Settings
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ px: 3, pb: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Contact Page Title"
                  value={settingsForm.contact_title || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, contact_title: e.target.value })}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Contact Page Description"
                  multiline
                  rows={3}
                  value={settingsForm.contact_description || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, contact_description: e.target.value })}
                  margin="normal"
                />
              </Grid>
            </Grid>
            {expandedAccordion === 'contact' && (
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  startIcon={saving === 'contact' ? <CircularProgress size={20} /> : <SaveIcon />}
                  onClick={() => handleSaveSettings('contact')}
                  disabled={saving === 'contact'}
                >
                  Save Contact Settings
                </Button>
              </Box>
            )}
          </AccordionDetails>
        </Accordion>

        {/* Contact & Social Media */}
        <Accordion 
          expanded={expandedAccordion === 'social'}
          onChange={handleAccordionChange('social')}
          sx={{ 
            mb: 2,
            borderRadius: 1,
            '&:before': { display: 'none' },
            boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
            transition: 'all 0.3s ease-in-out',
          }}
        >
          <AccordionSummary 
            expandIcon={<ExpandMoreIcon />}
            sx={{ px: 2, py: 1.5 }}
          >
            <Typography variant="h6" sx={{ fontWeight: 500 }}>
              Contact & Social Media
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ px: 3, pb: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Contact Email"
                  type="email"
                  value={settingsForm.contact_email || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, contact_email: e.target.value })}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Contact Phone"
                  value={settingsForm.contact_phone || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, contact_phone: e.target.value })}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Twitter URL"
                  type="url"
                  value={settingsForm.twitter_url || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, twitter_url: e.target.value })}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="LinkedIn URL"
                  type="url"
                  value={settingsForm.linkedin_url || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, linkedin_url: e.target.value })}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Instagram URL"
                  type="url"
                  value={settingsForm.instagram_url || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, instagram_url: e.target.value })}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Facebook URL"
                  type="url"
                  value={settingsForm.facebook_url || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, facebook_url: e.target.value })}
                  margin="normal"
                />
              </Grid>
            </Grid>
            {expandedAccordion === 'social' && (
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  startIcon={saving === 'social' ? <CircularProgress size={20} /> : <SaveIcon />}
                  onClick={() => handleSaveSettings('social')}
                  disabled={saving === 'social'}
                >
                  Save Social Media Settings
                </Button>
              </Box>
            )}
          </AccordionDetails>
        </Accordion>

        {/* API Keys */}
        <Accordion 
          expanded={expandedAccordion === 'api-keys'}
          onChange={handleAccordionChange('api-keys')}
          sx={{ 
            mb: 2,
            borderRadius: 1,
            '&:before': { display: 'none' },
            boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
            transition: 'all 0.3s ease-in-out',
          }}
        >
          <AccordionSummary 
            expandIcon={<ExpandMoreIcon />}
            sx={{ px: 2, py: 1.5 }}
          >
            <Typography variant="h6" sx={{ fontWeight: 500 }}>
              API Keys
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ px: 3, pb: 3 }}>
            <Alert severity="warning" sx={{ mb: 3 }}>
              API keys are masked for security. Enter a new key to update it.
            </Alert>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="OpenAI API Key"
                  type={showPasswords['openai'] ? 'text' : 'password'}
                  value={settingsForm.openai_api_key || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, openai_api_key: e.target.value })}
                  margin="normal"
                  helperText={systemSettings?.openai_api_key_masked ? `Current: ${systemSettings.openai_api_key_masked}` : 'Not set'}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowPasswords({ ...showPasswords, openai: !showPasswords['openai'] })}
                          edge="end"
                        >
                          {showPasswords['openai'] ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Stripe API Key"
                  type={showPasswords['stripe'] ? 'text' : 'password'}
                  value={settingsForm.stripe_api_key || settingsForm.stripe_secret_key || ''}
                  onChange={(e) => setSettingsForm({ 
                    ...settingsForm, 
                    stripe_api_key: e.target.value,
                    stripe_secret_key: e.target.value,
                  })}
                  margin="normal"
                  helperText={systemSettings?.stripe_api_key_masked || systemSettings?.stripe_secret_key_masked 
                    ? `Current: ${systemSettings.stripe_api_key_masked || systemSettings.stripe_secret_key_masked}` 
                    : 'Not set'}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowPasswords({ ...showPasswords, stripe: !showPasswords['stripe'] })}
                          edge="end"
                        >
                          {showPasswords['stripe'] ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="SMTP API Key"
                  type={showPasswords['smtp'] ? 'text' : 'password'}
                  value={settingsForm.smtp_api_key || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, smtp_api_key: e.target.value })}
                  margin="normal"
                  helperText={systemSettings?.smtp_api_key_masked ? `Current: ${systemSettings.smtp_api_key_masked}` : 'Not set'}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowPasswords({ ...showPasswords, smtp: !showPasswords['smtp'] })}
                          edge="end"
                        >
                          {showPasswords['smtp'] ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
            </Grid>
            {expandedAccordion === 'api-keys' && (
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  startIcon={saving === 'api-keys' ? <CircularProgress size={20} /> : <SaveIcon />}
                  onClick={() => handleSaveSettings('api-keys')}
                  disabled={saving === 'api-keys'}
                >
                  Save API Keys
                </Button>
              </Box>
            )}
          </AccordionDetails>
        </Accordion>

        {/* Email Configuration */}
        <Accordion 
          expanded={expandedAccordion === 'email'}
          onChange={handleAccordionChange('email')}
          sx={{ 
            mb: 2,
            borderRadius: 1,
            '&:before': { display: 'none' },
            boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
            transition: 'all 0.3s ease-in-out',
          }}
        >
          <AccordionSummary 
            expandIcon={<ExpandMoreIcon />}
            sx={{ px: 2, py: 1.5 }}
          >
            <Typography variant="h6" sx={{ fontWeight: 500 }}>
              Email Configuration
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ px: 3, pb: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="SMTP Host"
                  value={settingsForm.smtp_host || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, smtp_host: e.target.value })}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="SMTP Port"
                  type="number"
                  value={settingsForm.smtp_port || 587}
                  onChange={(e) => setSettingsForm({ ...settingsForm, smtp_port: parseInt(e.target.value) || 587 })}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="SMTP Username"
                  value={settingsForm.smtp_username || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, smtp_username: e.target.value })}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="SMTP Password"
                  type={showPasswords['smtp_password'] ? 'text' : 'password'}
                  value={settingsForm.smtp_password || ''}
                  onChange={(e) => setSettingsForm({ ...settingsForm, smtp_password: e.target.value })}
                  margin="normal"
                  helperText={systemSettings?.smtp_password_masked ? `Current: ${systemSettings.smtp_password_masked}` : 'Not set'}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowPasswords({ ...showPasswords, smtp_password: !showPasswords['smtp_password'] })}
                          edge="end"
                        >
                          {showPasswords['smtp_password'] ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Switch
                    checked={settingsForm.enable_tls || false}
                    onChange={(e) => setSettingsForm({ ...settingsForm, enable_tls: e.target.checked })}
                  />
                  <Typography>Enable TLS</Typography>
                </Box>
              </Grid>
            </Grid>
            {expandedAccordion === 'email' && (
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  startIcon={saving === 'email' ? <CircularProgress size={20} /> : <SaveIcon />}
                  onClick={() => handleSaveSettings('email')}
                  disabled={saving === 'email'}
                >
                  Save Email Settings
                </Button>
              </Box>
            )}
          </AccordionDetails>
        </Accordion>
      </Paper>

      {/* SECTION 3: System Actions */}
      <Paper 
        sx={{ 
          p: 3, 
          mb: 3,
          borderRadius: 2,
          boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
        }}
      >
        <Typography 
          variant="h5" 
          gutterBottom 
          sx={{ 
            fontWeight: 600, 
            mb: 3,
            textAlign: 'left',
          }}
        >
          System Actions
        </Typography>
        <Grid container spacing={2}>
          {/* Row 1 */}
          <Grid item xs={12} sm={6} md={6}>
            <Button
              fullWidth
              variant="contained"
              color="primary"
              startIcon={actionLoading === 'clear-cache' ? <CircularProgress size={20} color="inherit" /> : <RefreshIcon />}
              onClick={() => handleSystemAction('clear-cache')}
              disabled={actionLoading === 'clear-cache'}
              sx={{ py: 1.5, fontSize: '0.95rem' }}
            >
              Clear Cache
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={6}>
            <Button
              fullWidth
              variant="contained"
              color="primary"
              startIcon={actionLoading === 'reset-rate-limits' ? <CircularProgress size={20} color="inherit" /> : <RefreshIcon />}
              onClick={() => handleSystemAction('reset-rate-limits')}
              disabled={actionLoading === 'reset-rate-limits'}
              sx={{ py: 1.5, fontSize: '0.95rem' }}
            >
              Reset Rate Limits
            </Button>
          </Grid>
          {/* Row 2 */}
          <Grid item xs={12} sm={6} md={6}>
            <Button
              fullWidth
              variant="contained"
              color="primary"
              startIcon={actionLoading === 'rebuild-index' ? <CircularProgress size={20} color="inherit" /> : <RefreshIcon />}
              onClick={() => handleSystemAction('rebuild-index')}
              disabled={actionLoading === 'rebuild-index'}
              sx={{ py: 1.5, fontSize: '0.95rem' }}
            >
              Rebuild Search Index
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={6}>
            <Button
              fullWidth
              variant="contained"
              color="error"
              startIcon={actionLoading === 'error-logs' ? <CircularProgress size={20} color="inherit" /> : <VisibilityIcon />}
              onClick={() => handleSystemAction('error-logs')}
              disabled={actionLoading === 'error-logs'}
              sx={{ py: 1.5, fontSize: '0.95rem' }}
            >
              View Error Logs
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* SECTION 4: Audit Logs */}
      <Paper 
        sx={{ 
          p: 3,
          borderRadius: 2,
          boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
        }}
      >
        <Typography 
          variant="h5" 
          gutterBottom 
          sx={{ 
            fontWeight: 600, 
            mb: 3,
            textAlign: 'left',
          }}
        >
          Audit Logs
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
          <TextField
            label="Admin User"
            value={auditFilters.admin_user}
            onChange={(event) => setAuditFilters(prev => ({ ...prev, admin_user: event.target.value }))}
          />
          <TextField
            label="Action Type"
            value={auditFilters.action_type}
            onChange={(event) => setAuditFilters(prev => ({ ...prev, action_type: event.target.value }))}
          />
          <TextField
            label="From"
            type="date"
            value={auditFilters.date_from}
            onChange={(event) => setAuditFilters(prev => ({ ...prev, date_from: event.target.value }))}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="To"
            type="date"
            value={auditFilters.date_to}
            onChange={(event) => setAuditFilters(prev => ({ ...prev, date_to: event.target.value }))}
            InputLabelProps={{ shrink: true }}
          />
          <Button
            variant="contained"
            onClick={fetchAuditLogs}
            disabled={auditLoading}
          >
            {auditLoading ? 'Loading...' : 'Load Logs'}
          </Button>
        </Box>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Time</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Admin</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Action</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Description</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Target</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {auditLogs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 6, bgcolor: 'grey.50' }}>
                    <Typography variant="body2" color="text.secondary">
                      No audit logs recorded yet.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                auditLogs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>{log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}</TableCell>
                    <TableCell>{log.admin_user || 'N/A'}</TableCell>
                    <TableCell>{log.action_type_display || log.action_type}</TableCell>
                    <TableCell>{log.action_description}</TableCell>
                    <TableCell>{log.target_model ? `${log.target_model} ${log.target_id || ''}` : 'N/A'}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Error Logs Dialog */}
      <Dialog
        open={errorLogsOpen}
        onClose={() => setErrorLogsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Error Logs</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            Recent error logs from the system
          </DialogContentText>
          <Box
            sx={{
              maxHeight: 400,
              overflow: 'auto',
              bgcolor: 'grey.50',
              p: 2,
              borderRadius: 1,
            }}
          >
            {errorLogs.length > 0 ? (
              errorLogs.map((log, index) => (
                <Typography
                  key={index}
                  variant="body2"
                  component="pre"
                  sx={{
                    fontFamily: 'monospace',
                    fontSize: '0.75rem',
                    mb: 1,
                    color: 'error.main',
                  }}
                >
                  {log}
                </Typography>
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">
                No error logs found
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setErrorLogsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default SystemPage;
