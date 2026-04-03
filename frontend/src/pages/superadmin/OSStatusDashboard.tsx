import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Alert,
  Paper,
  Divider,
  Button,
} from '@mui/material';
import {
  Security as SecurityIcon,
  CheckCircle as CheckCircleIcon,
  Block as BlockIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import { handleApiError } from '../../services/utils/errorHandler';
import type { ApiError } from '../../services/utils/errorHandler';
import apiClient from '../../services/api/client';

interface PlatformState {
  id: string;
  state: string;
  active_workloads: string[];
  frozen_modules: string[];
  governance_version: number;
  reason: string;
  updated_by: string | null;
  updated_at: string;
  created_at: string;
}

interface FeatureFlag {
  id: string;
  key: string;
  state: 'OFF' | 'BETA' | 'ON';
  visibility: string;
  rollout_rule: any;
  reason: string;
  updated_by: string | null;
  updated_at: string;
}

const OSStatusDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [platformState, setPlatformState] = useState<PlatformState | null>(null);
  const [featureFlags, setFeatureFlags] = useState<FeatureFlag[]>([]);

  // Check if user is superuser
  const isSuperUser = Boolean(user?.is_superuser);

  useEffect(() => {
    const fetchGovernanceData = async () => {
      if (!isSuperUser) {
        navigate('/admin');
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const [stateResponse, flagsResponse] = await Promise.all([
          apiClient.get('/api/v1/adminpanel/governance/platform-state/'),
          apiClient.get('/api/v1/adminpanel/governance/feature-flags/'),
        ]);

        setPlatformState(stateResponse.data);
        setFeatureFlags(flagsResponse.data);
      } catch (err: any) {
        console.error('Failed to fetch governance data:', err);
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };

    fetchGovernanceData();
  }, [isSuperUser, navigate]);

  if (loading) {
    return <LoadingSpinner message="Loading OS Status..." />;
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <ErrorAlert error={error} overrideMessage="Failed to load OS governance data." />
      </Container>
    );
  }

  if (!platformState) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error">
          Platform governance not initialized. Please run: python manage.py kernel_init_governance
        </Alert>
      </Container>
    );
  }

  // Get active and frozen modules from feature flags
  const activeModules = featureFlags.filter(f => f.state === 'ON');
  const betaModules = featureFlags.filter(f => f.state === 'BETA');
  const frozenModules = featureFlags.filter(f => f.state === 'OFF');

  // Get state color
  const getStateColor = (state: string) => {
    switch (state) {
      case 'SINGLE_WORKLOAD':
        return 'warning';
      case 'MULTI_WORKLOAD':
        return 'info';
      case 'MAINTENANCE':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* OS Warning Banner */}
      <Alert 
        severity="warning" 
        icon={<SecurityIcon />}
        sx={{ mb: 4, fontWeight: 600 }}
      >
        ⚠️ You are operating the CareerBridge OS Kernel. All actions are audited.
      </Alert>

      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          CareerBridge OS Status
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Platform governance and module status overview
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Platform State Card */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <SecurityIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" fontWeight="bold">
                  Platform State
                </Typography>
              </Box>

              <Box sx={{ mb: 3 }}>
                <Chip 
                  label={platformState.state} 
                  color={getStateColor(platformState.state) as any}
                  sx={{ fontWeight: 600, fontSize: '0.9rem', px: 1 }}
                />
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Governance Version:
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  v{platformState.governance_version}
                </Typography>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Updated By:
                </Typography>
                <Typography variant="body1">
                  {platformState.updated_by || 'System'}
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Last Updated:
                </Typography>
                <Typography variant="body2">
                  {new Date(platformState.updated_at).toLocaleString()}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Active Workloads Card */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <CheckCircleIcon sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6" fontWeight="bold">
                  Active Workloads
                </Typography>
              </Box>

              {platformState.active_workloads.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No active workloads
                </Typography>
              ) : (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {platformState.active_workloads.map((workload) => (
                    <Chip
                      key={workload}
                      label={workload}
                      color="success"
                      variant="outlined"
                      size="medium"
                    />
                  ))}
                </Box>
              )}

              <Divider sx={{ my: 2 }} />

              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Active Modules ({activeModules.length}):
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                  {activeModules.map((flag) => (
                    <Chip
                      key={flag.key}
                      label={flag.key}
                      size="small"
                      color="success"
                      sx={{ fontSize: '0.75rem' }}
                    />
                  ))}
                </Box>
              </Box>

              {betaModules.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Beta Modules ({betaModules.length}):
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                    {betaModules.map((flag) => (
                      <Chip
                        key={flag.key}
                        label={flag.key}
                        size="small"
                        color="warning"
                        sx={{ fontSize: '0.75rem' }}
                      />
                    ))}
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Frozen Modules Card */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <BlockIcon sx={{ mr: 1, color: 'error.main' }} />
                <Typography variant="h6" fontWeight="bold" color="error.main">
                  Frozen Modules (Phase-A)
                </Typography>
              </Box>

              <Alert severity="error" sx={{ mb: 2 }}>
                The following modules are FROZEN and will return HTTP 404. All commercial features are disabled for Phase-A.
              </Alert>

              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {frozenModules.map((flag) => (
                  <Chip
                    key={flag.key}
                    label={flag.key}
                    color="error"
                    variant="outlined"
                    size="small"
                  />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* State Reason Card */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <HistoryIcon sx={{ mr: 1, color: 'text.secondary' }} />
                <Typography variant="h6" fontWeight="bold">
                  Current State Reason
                </Typography>
              </Box>

              <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="body1">
                  {platformState.reason}
                </Typography>
              </Paper>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Kernel Controls
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<SettingsIcon />}
                  onClick={() => navigate('/superadmin/governance')}
                >
                  Platform Control Center
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<HistoryIcon />}
                  onClick={() => navigate('/superadmin/audit/governance')}
                >
                  View Audit Logs
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default OSStatusDashboard;
