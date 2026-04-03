import React, { useEffect, useState, useCallback } from 'react';

import apiClient from '../../services/api/client';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Snackbar,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';



interface BusPowerState {
  bus_name: string;
  state: string;
  reason: string;
  updated_at: string | null;
}

interface FeatureFlag {
  id: number;
  key: string;
  state: string;
  visibility: string;
  rollout_rule: string | null;
  reason: string;
  updated_at: string | null;
}

interface Capability {
  id: string;
  label: string;
  icon: string;
  bus: string;
  locked?: boolean;
  flags: string[];
  flagVisibility: Record<string, string>;
}

const CAPABILITIES: Capability[] = [
  {
    id: 'KERNEL_CORE',
    label: 'Kernel Core',
    icon: '⚙️',
    bus: 'KERNEL_CORE_BUS',
    locked: true,
    flags: ['KERNEL_ADMIN', 'USERS'],
    flagVisibility: { KERNEL_ADMIN: 'internal', USERS: 'user' },
  },
  {
    id: 'AI',
    label: 'AI Capability',
    icon: '🤖',
    bus: 'AI_BUS',
    flags: ['ATS_SIGNALS', 'SIGNAL_DELIVERY', 'ENGINES_SIGNAL_CORE', 'ENGINES_JOB_INGESTION'],
    flagVisibility: { ATS_SIGNALS: 'user', SIGNAL_DELIVERY: 'user', ENGINES_SIGNAL_CORE: 'internal', ENGINES_JOB_INGESTION: 'internal' },
  },
  {
    id: 'ADMIN',
    label: 'Admin Operations',
    icon: '🔧',
    bus: 'ADMIN_BUS',
    flags: [],
    flagVisibility: {},
  },
  {
    id: 'MENTOR',
    label: 'Mentor / Human-Loop',
    icon: '👥',
    bus: 'MENTOR_BUS',
    flags: ['HUMAN_LOOP', 'DECISION_SLOTS', 'APPOINTMENTS', 'MENTORS'],
    flagVisibility: { HUMAN_LOOP: 'user', DECISION_SLOTS: 'user', APPOINTMENTS: 'user', MENTORS: 'user' },
  },
  {
    id: 'PAYMENT',
    label: 'Payment',
    icon: '💳',
    bus: 'PAYMENT_BUS',
    flags: ['PAYMENTS'],
    flagVisibility: { PAYMENTS: 'user' },
  },
  {
    id: 'SEARCH',
    label: 'Search / Discovery',
    icon: '🔍',
    bus: 'SEARCH_BUS',
    flags: ['SEARCH', 'JOB_CRAWLER'],
    flagVisibility: { SEARCH: 'user', JOB_CRAWLER: 'internal' },
  },
  {
    id: 'PEER_MOCK',
    label: 'Peer Mock Runtime',
    icon: '🧪',
    bus: 'PEER_MOCK_BUS',
    flags: ['PEER_MOCK'],
    flagVisibility: { PEER_MOCK: 'user' },
  },
  {
    id: 'PUBLIC_WEB',
    label: 'Public Web',
    icon: '🌐',
    bus: 'PUBLIC_WEB_BUS',
    flags: [],
    flagVisibility: {},
  },
];

const GovernanceControlPage: React.FC = () => {
  const [buses, setBuses] = useState<BusPowerState[]>([]);
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [loading, setLoading] = useState(true);

  // Per-bus toggle loading
  const [busTogglingId, setBusTogglingId] = useState<string | null>(null);
  // Per-flag toggle loading
  const [flagTogglingKey, setFlagTogglingKey] = useState<string | null>(null);
  // Per-capability quick action loading
  const [quickActionId, setQuickActionId] = useState<string | null>(null);

  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const fetchData = useCallback(async () => {
    try {
      const [busRes, flagRes] = await Promise.all([
        apiClient.get('/kernel/console/buses/'),
        apiClient.get('/kernel/console/flags/'),
      ]);
      setBuses(busRes.data);
      setFlags(flagRes.data);
    } catch (err) {
      setSnackbar({ open: true, message: 'Failed to load governance data', severity: 'error' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getBusState = (busName: string) => {
    const b = buses.find(b => b.bus_name === busName);
    return b?.state ?? 'OFF';
  };

  const getFlagState = (key: string) => {
    const f = flags.find(f => f.key === key);
    return f?.state ?? 'OFF';
  };

  const toggleBus = async (busName: string, currentState: string) => {
    if (busName === 'KERNEL_CORE_BUS') return;
    setBusTogglingId(busName);
    const newState = currentState === 'ON' ? 'OFF' : 'ON';
    try {
      await apiClient.patch('/kernel/console/buses/', { [busName]: newState });
      setBuses(prev => prev.map(b => b.bus_name === busName ? { ...b, state: newState } : b));
      setSnackbar({ open: true, message: `${busName} turned ${newState}`, severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: `Failed to toggle ${busName}`, severity: 'error' });
    } finally {
      setBusTogglingId(null);
    }
  };

  const toggleFlag = async (key: string, currentState: string, visibility: string) => {
    setFlagTogglingKey(key);
    const newState = currentState === 'ON' ? 'OFF' : 'ON';
    try {
      await apiClient.patch('/kernel/console/flags/', { [key]: { state: newState, visibility } });
      setFlags(prev => prev.map(f => f.key === key ? { ...f, state: newState, visibility } : f));
      setSnackbar({ open: true, message: `${key} turned ${newState}`, severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: `Failed to toggle ${key}`, severity: 'error' });
    } finally {
      setFlagTogglingKey(null);
    }
  };

  const handleFullOn = async (cap: Capability) => {
    if (cap.locked) return;
    setQuickActionId(`${cap.id}-on`);
    try {
      const busPromise = apiClient.patch('/kernel/console/buses/', { [cap.bus]: 'ON' });

      const flagPayload: Record<string, { state: string; visibility: string }> = {};
      cap.flags.forEach(key => {
        flagPayload[key] = { state: 'ON', visibility: cap.flagVisibility[key] };
      });

      const promises: Promise<any>[] = [busPromise];
      if (Object.keys(flagPayload).length > 0) {
        promises.push(apiClient.patch('/kernel/console/flags/', flagPayload));
      }

      await Promise.all(promises);
      setBuses(prev => prev.map(b => b.bus_name === cap.bus ? { ...b, state: 'ON' } : b));
      setFlags(prev => prev.map(f => {
        if (cap.flags.includes(f.key)) {
          return { ...f, state: 'ON', visibility: (cap.flagVisibility as Record<string, string>)[f.key] || f.visibility };
        }
        return f;
      }));
      setSnackbar({ open: true, message: `${cap.label}: all enabled`, severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: `Failed to enable ${cap.label}`, severity: 'error' });
    } finally {
      setQuickActionId(null);
    }
  };

  const handleFullOff = async (cap: Capability) => {
    if (cap.locked) return;
    setQuickActionId(`${cap.id}-off`);
    try {
      const busPromise = apiClient.patch('/kernel/console/buses/', { [cap.bus]: 'OFF' });

      const flagPayload: Record<string, { state: string; visibility: string }> = {};
      cap.flags.forEach(key => {
        flagPayload[key] = { state: 'OFF', visibility: cap.flagVisibility[key] };
      });

      const promises: Promise<any>[] = [busPromise];
      if (Object.keys(flagPayload).length > 0) {
        promises.push(apiClient.patch('/kernel/console/flags/', flagPayload));
      }

      await Promise.all(promises);
      setBuses(prev => prev.map(b => b.bus_name === cap.bus ? { ...b, state: 'OFF' } : b));
      setFlags(prev => prev.map(f => {
        if (cap.flags.includes(f.key)) {
          return { ...f, state: 'OFF' };
        }
        return f;
      }));
      setSnackbar({ open: true, message: `${cap.label}: all disabled`, severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: `Failed to disable ${cap.label}`, severity: 'error' });
    } finally {
      setQuickActionId(null);
    }
  };

  const busesOnCount = buses.filter(b => b.state === 'ON').length;
  const flagsOnCount = flags.filter(f => f.state === 'ON').length;

  const getFlagChipColor = (state: string): 'success' | 'error' | 'warning' => {
    if (state === 'ON') return 'success';
    if (state === 'BETA') return 'warning';
    return 'error';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Typography variant="h4" fontWeight={700} gutterBottom>
        Governance Control
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Manage Bus Power and Feature Flags for all capabilities
      </Typography>

      {/* Summary Bar */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack direction="row" spacing={4}>
          <Box>
            <Typography variant="caption" color="text.secondary">Total Capabilities</Typography>
            <Typography variant="h6" fontWeight={700}>{CAPABILITIES.length}</Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">Buses ON</Typography>
            <Typography variant="h6" fontWeight={700} color="success.main">{busesOnCount}</Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">Flags ON</Typography>
            <Typography variant="h6" fontWeight={700} color="success.main">{flagsOnCount}</Typography>
          </Box>
        </Stack>
      </Paper>

      {/* Capability Table */}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 700, minWidth: 180 }}>Capability</TableCell>
              <TableCell sx={{ fontWeight: 700, minWidth: 140 }}>Bus Power</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Feature Flags</TableCell>
              <TableCell sx={{ fontWeight: 700, minWidth: 180 }}>Quick Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {CAPABILITIES.map(cap => {
              const busState = getBusState(cap.bus);
              const isBusToggling = busTogglingId === cap.bus;
              const isLocked = cap.locked === true;

              return (
                <TableRow key={cap.id} hover>
                  {/* Capability Label */}
                  <TableCell>
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <Typography fontSize="1.2rem">{cap.icon}</Typography>
                      <Typography variant="body2" fontWeight={600}>{cap.label}</Typography>
                    </Stack>
                  </TableCell>

                  {/* Bus Power Toggle */}
                  <TableCell>
                    <Stack direction="row" alignItems="center" spacing={1}>
                      {isBusToggling ? (
                        <CircularProgress size={20} />
                      ) : (
                        <Tooltip title={isLocked ? 'KERNEL_CORE_BUS is locked' : `${cap.bus}: ${busState}`}>
                          <span>
                            <Switch
                              checked={busState === 'ON'}
                              onChange={() => toggleBus(cap.bus, busState)}
                              disabled={isLocked || isBusToggling}
                              color="success"
                              size="small"
                            />
                          </span>
                        </Tooltip>
                      )}
                      <Typography variant="caption" color={busState === 'ON' ? 'success.main' : 'text.secondary'}>
                        {busState}
                      </Typography>
                    </Stack>
                  </TableCell>

                  {/* Feature Flags */}
                  <TableCell>
                    <Stack direction="row" flexWrap="wrap" gap={0.5}>
                      {cap.flags.length === 0 && (
                        <Typography variant="caption" color="text.disabled">—</Typography>
                      )}
                      {cap.flags.map(key => {
                        const flagState = getFlagState(key);
                        const isFlagToggling = flagTogglingKey === key;
                        const visibility = cap.flagVisibility[key];

                        return (
                          <Tooltip key={key} title={`${key} · ${flagState} · ${visibility}`}>
                            <span>
                              {isFlagToggling ? (
                                <Box
                                  sx={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    width: 24,
                                    height: 24,
                                  }}
                                >
                                  <CircularProgress size={16} />
                                </Box>
                              ) : (
                                <Chip
                                  label={key}
                                  size="small"
                                  color={getFlagChipColor(flagState)}
                                  variant={flagState === 'ON' ? 'filled' : 'outlined'}
                                  onClick={() => toggleFlag(key, flagState, visibility)}
                                  sx={{ cursor: 'pointer', fontSize: '0.7rem' }}
                                />
                              )}
                            </span>
                          </Tooltip>
                        );
                      })}
                    </Stack>
                  </TableCell>

                  {/* Quick Actions */}
                  <TableCell>
                    <Stack direction="row" spacing={1}>
                      <Button
                        size="small"
                        variant="contained"
                        color="success"
                        disabled={isLocked || quickActionId === `${cap.id}-on`}
                        onClick={() => handleFullOn(cap)}
                        startIcon={quickActionId === `${cap.id}-on` ? <CircularProgress size={14} color="inherit" /> : undefined}
                        sx={{ fontSize: '0.7rem', py: 0.5 }}
                      >
                        Full ON
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        disabled={isLocked || quickActionId === `${cap.id}-off`}
                        onClick={() => handleFullOff(cap)}
                        startIcon={quickActionId === `${cap.id}-off` ? <CircularProgress size={14} color="inherit" /> : undefined}
                        sx={{ fontSize: '0.7rem', py: 0.5 }}
                      >
                        Full OFF
                      </Button>
                    </Stack>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar(s => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar(s => ({ ...s, open: false }))}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default GovernanceControlPage;
