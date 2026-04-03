import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  Switch,
  CircularProgress,
  Divider,
  Paper,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  ElectricBolt as BusIcon,
  Lock as LockIcon,
  Psychology as AIIcon,
  AdminPanelSettings as AdminIcon,
  Public as PublicIcon,
  People as MentorIcon,
  Payment as PaymentIcon,
  Search as SearchIcon,
  Science as MockIcon,
  CheckCircle as OnIcon,
  Cancel as OffIcon,
} from '@mui/icons-material';
import apiClient from '../../services/api/client';

// ── Types ─────────────────────────────────────────────────────────────────────

interface BusState {
  bus_name: string;
  state: 'ON' | 'OFF';
  reason: string;
  updated_at: string | null;
}

// ── Bus metadata ──────────────────────────────────────────────────────────────

const BUS_META: Record<string, { label: string; description: string; icon: React.ReactElement; locked?: boolean }> = {
  KERNEL_CORE_BUS: {
    label: 'Kernel Core',
    description: 'OS control plane — always ON, immutable',
    icon: <LockIcon />,
    locked: true,
  },
  AI_BUS: {
    label: 'AI Capability',
    description: 'ATS signals, engines, decision slots, chat',
    icon: <AIIcon />,
  },
  ADMIN_BUS: {
    label: 'Admin Operations',
    description: 'Staff, audit, ops console',
    icon: <AdminIcon />,
  },
  PUBLIC_WEB_BUS: {
    label: 'Public Web',
    description: 'Marketing and landing pages',
    icon: <PublicIcon />,
  },
  MENTOR_BUS: {
    label: 'Mentor / Human-Loop',
    description: 'Appointments, availability, mentors',
    icon: <MentorIcon />,
  },
  PAYMENT_BUS: {
    label: 'Payment / Transaction',
    description: 'Stripe, billing',
    icon: <PaymentIcon />,
  },
  SEARCH_BUS: {
    label: 'Search / Discovery',
    description: 'Search, analytics',
    icon: <SearchIcon />,
  },
  PEER_MOCK_BUS: {
    label: 'Peer Mock Runtime',
    description: 'Simulation and testing',
    icon: <MockIcon />,
  },
};

// ── Component ─────────────────────────────────────────────────────────────────

const BusPowerPage: React.FC = () => {
  const [buses, setBuses] = useState<BusState[]>([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false, message: '', severity: 'success',
  });

  // Load buses
  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const res = await apiClient.get('/kernel/console/buses/');
        setBuses(res.data);
      } catch (e: any) {
        setError(e?.response?.data?.detail || 'Failed to load bus states');
      } finally {
        setLoading(false);
      }
    };
    fetch();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Toggle a bus
  const handleToggle = async (busName: string, currentState: 'ON' | 'OFF') => {
    if (busName === 'KERNEL_CORE_BUS') return;
    const newState = currentState === 'ON' ? 'OFF' : 'ON';

    setToggling(prev => ({ ...prev, [busName]: true }));
    try {
      const res = await apiClient.patch('/kernel/console/buses/', { [busName]: newState });

      if (res.data.errors?.length) {
        setToast({ open: true, message: res.data.errors[0], severity: 'error' });
      } else {
        setBuses(prev => prev.map(b => b.bus_name === busName ? { ...b, state: newState } : b));
        setToast({ open: true, message: `${BUS_META[busName]?.label ?? busName} turned ${newState}`, severity: 'success' });
      }
    } catch (e: any) {
      setToast({ open: true, message: e?.response?.data?.detail || 'Update failed', severity: 'error' });
    } finally {
      setToggling(prev => ({ ...prev, [busName]: false }));
    }
  };

  const onCount = buses.filter(b => b.state === 'ON').length;
  const totalCount = buses.length;

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'grey.50' }}>

      {/* ── Header ── */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          py: 4,
          px: 3,
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
            <BusIcon sx={{ fontSize: 32 }} />
            <Typography variant="h4" fontWeight={700}>
              Bus Power Control
            </Typography>
          </Box>
          <Typography variant="body1" sx={{ opacity: 0.85 }}>
            Only SuperAdmin can enable or disable capability buses. Changes take effect immediately.
          </Typography>
        </Container>
      </Box>

      <Container maxWidth="lg" sx={{ py: 4 }}>

        {/* ── Summary bar ── */}
        <Paper
          elevation={0}
          sx={{
            p: 2.5,
            mb: 3,
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 2,
            display: 'flex',
            alignItems: 'center',
            gap: 3,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <OnIcon sx={{ color: 'success.main' }} />
            <Typography variant="h6" fontWeight={700} color="success.main">
              {onCount}
            </Typography>
            <Typography variant="body2" color="text.secondary">buses ON</Typography>
          </Box>
          <Divider orientation="vertical" flexItem />
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <OffIcon sx={{ color: 'error.light' }} />
            <Typography variant="h6" fontWeight={700} color="error.main">
              {totalCount - onCount}
            </Typography>
            <Typography variant="body2" color="text.secondary">buses OFF</Typography>
          </Box>
          <Divider orientation="vertical" flexItem />
          <Typography variant="body2" color="text.secondary">
            {totalCount} total buses
          </Typography>
        </Paper>

        {/* ── Error state ── */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
        )}

        {/* ── Loading ── */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Grid container spacing={2}>
            {buses.map((bus) => {
              const meta = BUS_META[bus.bus_name];
              const isOn = bus.state === 'ON';
              const isLocked = meta?.locked === true;
              const isLoading = toggling[bus.bus_name];

              return (
                <Grid item xs={12} sm={6} key={bus.bus_name}>
                  <Card
                    elevation={0}
                    sx={{
                      border: '1px solid',
                      borderColor: isOn ? 'success.light' : 'divider',
                      borderRadius: 2,
                      transition: 'border-color 0.2s',
                      opacity: isLocked ? 0.85 : 1,
                    }}
                  >
                    <CardContent sx={{ p: 2.5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>

                        {/* Left: icon + name + description */}
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                          <Box
                            sx={{
                              p: 1,
                              borderRadius: 1.5,
                              bgcolor: isOn ? 'success.50' : 'grey.100',
                              color: isOn ? 'success.main' : 'text.secondary',
                              display: 'flex',
                              alignItems: 'center',
                            }}
                          >
                            {meta?.icon}
                          </Box>
                          <Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.25 }}>
                              <Typography variant="subtitle1" fontWeight={600}>
                                {meta?.label ?? bus.bus_name}
                              </Typography>
                              <Chip
                                label={bus.state}
                                size="small"
                                sx={{
                                  bgcolor: isOn ? 'success.main' : 'error.main',
                                  color: 'white',
                                  fontWeight: 700,
                                  fontSize: '0.65rem',
                                  height: 20,
                                }}
                              />
                            </Box>
                            <Typography variant="caption" color="text.secondary">
                              {meta?.description}
                            </Typography>
                            {bus.updated_at && (
                              <Typography variant="caption" display="block" color="text.disabled" sx={{ mt: 0.5 }}>
                                Updated {new Date(bus.updated_at).toLocaleString()}
                              </Typography>
                            )}
                          </Box>
                        </Box>

                        {/* Right: toggle or spinner */}
                        <Box sx={{ display: 'flex', alignItems: 'center', ml: 1, mt: 0.5 }}>
                          {isLoading ? (
                            <CircularProgress size={24} />
                          ) : (
                            <Switch
                              checked={isOn}
                              disabled={isLocked}
                              onChange={() => handleToggle(bus.bus_name, bus.state)}
                              color="success"
                              size="small"
                            />
                          )}
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        )}
      </Container>

      {/* ── Toast ── */}
      <Snackbar
        open={toast.open}
        autoHideDuration={3000}
        onClose={() => setToast(t => ({ ...t, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity={toast.severity}
          onClose={() => setToast(t => ({ ...t, open: false }))}
          sx={{ width: '100%' }}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default BusPowerPage;
