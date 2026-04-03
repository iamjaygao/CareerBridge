/**
 * Workload Runtime Console - Bus Grouped View
 * 
 * Phase-A.2: Bus-grouped workload registry viewer
 * 
 * Purpose:
 * - Display frozen workloads grouped by Bus (capability domain)
 * - Bus as primary dimension with ON/OFF state
 * - Zero 404 noise: reads static bus registry file only
 * 
 * Constraints:
 * - NO runtime API calls to frozen modules
 * - NO actual unfreezing (Phase-A freeze policy is immutable)
 * - Read-only observability plane
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../services/api/client';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Stack,
  Switch,
  Snackbar,
} from '@mui/material';
import {
  ExpandMore,
  Refresh,
  Code,
  Rocket,
} from '@mui/icons-material';

interface WorkloadSignals {
  code_refs: string[];
  keywords: string[];
}

interface Workload {
  name: string;
  kind: 'backend' | 'frontend' | 'fullstack';
  world: 'public' | 'app' | 'admin' | 'kernel';
  status: 'FROZEN' | 'ACTIVE' | 'UNKNOWN_FROZEN_SIGNAL';
  reason: string;
  entrypoints: {
    frontend_routes: string[];
    backend_prefixes: string[];
  };
  signals: WorkloadSignals;
}

interface BusData {
  state: 'ON' | 'OFF';
  workloads: Workload[];
}

interface Registry {
  version: string;
  generated_at: string;
  scan_summary: {
    total_workloads: number;
    total_buses: number;
    by_bus: Record<string, number>;
  };
  buses: Record<string, BusData>;
}

const WorkloadRuntimeConsolePage: React.FC = () => {
  const navigate = useNavigate();
  const [registry, setRegistry] = useState<Registry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedBuses, setExpandedBuses] = useState<Set<string>>(new Set());
  const [busStates, setBusStates] = useState<Record<string, 'ON' | 'OFF'>>({});
  const [togglingBus, setTogglingBus] = useState<string | null>(null);
  const [toast, setToast] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false, message: '', severity: 'success',
  });

  /**
   * Load registry from static file (no backend API call)
   */
  const loadRegistry = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/registry/WORKLOAD_FROZEN_BUS_REGISTRY.json');

      if (!response.ok) {
        throw new Error(`Failed to load registry: ${response.status}`);
      }

      const data = await response.json();
      setRegistry(data);
    } catch (err: any) {
      console.error('Failed to load registry:', err);
      setError(err.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Load live bus power states from kernel API
   */
  const loadBusStates = async () => {
    try {
      const res = await apiClient.get('/kernel/console/buses/');
      const map: Record<string, 'ON' | 'OFF'> = {};
      for (const bus of res.data) {
        map[bus.bus_name] = bus.state;
      }
      setBusStates(map);
    } catch (e) {
      // Silently fail — static registry state remains visible
      console.warn('Could not load live bus states:', e);
    }
  };

  /**
   * Toggle a bus ON/OFF via kernel API
   */
  const toggleBusPower = async (busId: string, currentState: 'ON' | 'OFF') => {
    if (busId === 'KERNEL_CORE_BUS') return;
    const newState = currentState === 'ON' ? 'OFF' : 'ON';
    setTogglingBus(busId);
    try {
      const res = await apiClient.patch('/kernel/console/buses/', { [busId]: newState });
      if (res.data.errors?.length) {
        setToast({ open: true, message: res.data.errors[0], severity: 'error' });
      } else {
        setBusStates(prev => ({ ...prev, [busId]: newState }));
        setToast({ open: true, message: `${busId.replace('_BUS', '')} turned ${newState}`, severity: 'success' });
      }
    } catch (e: any) {
      setToast({ open: true, message: e?.response?.data?.detail || 'Update failed', severity: 'error' });
    } finally {
      setTogglingBus(null);
    }
  };

  useEffect(() => {
    loadRegistry();
    loadBusStates();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Toggle bus expansion
   */
  const toggleBusExpansion = (busId: string) => {
    setExpandedBuses(prev => {
      const next = new Set(prev);
      if (next.has(busId)) {
        next.delete(busId);
      } else {
        next.add(busId);
      }
      return next;
    });
  };

  // Console route for each bus (shown as Rocket button when bus is ON)
  const BUS_CONSOLE_ROUTES: Record<string, { path: string; tooltip: string; color: string }> = {
    KERNEL_CORE_BUS:  { path: '/superadmin/kernel-pulse',             tooltip: 'Kernel Pulse Console',        color: '#4C6EF5' },
    AI_BUS:           { path: '/superadmin/bus-console/AI_BUS',       tooltip: 'AI Capability Console',       color: '#9333EA' },
    ADMIN_BUS:        { path: '/superadmin/bus-console/ADMIN_BUS',    tooltip: 'Admin Operations Console',    color: '#F59E0B' },
    PUBLIC_WEB_BUS:   { path: '/superadmin/bus-console/PUBLIC_WEB_BUS', tooltip: 'Public Web Console',        color: '#06B6D4' },
    MENTOR_BUS:       { path: '/superadmin/bus-console/MENTOR_BUS',   tooltip: 'Mentor Bus Console',          color: '#EC4899' },
    PAYMENT_BUS:      { path: '/superadmin/bus-console/PAYMENT_BUS',  tooltip: 'Payment Bus Console',         color: '#10B981' },
    SEARCH_BUS:       { path: '/superadmin/bus-console/SEARCH_BUS',   tooltip: 'Search & Discovery Console',  color: '#F97316' },
    PEER_MOCK_BUS:    { path: '/superadmin/peer-mock',                 tooltip: 'Peer Mock Console',           color: '#22C55E' },
  };

  /**
   * Get bus display name (remove _BUS suffix)
   */
  const getBusDisplayName = (busId: string) => {
    return busId.replace('_BUS', '');
  };

  /**
   * Get bus icon
   */
  const getBusIcon = (busId: string) => {
    if (busId.includes('KERNEL')) return '⚙️';
    if (busId.includes('PAYMENT')) return '💳';
    if (busId.includes('AI')) return '🤖';
    if (busId.includes('MENTOR')) return '👥';
    if (busId.includes('ADMIN')) return '🔧';
    if (busId.includes('SEARCH')) return '🔍';
    if (busId.includes('CHAT')) return '💬';
    if (busId.includes('PUBLIC')) return '🌐';
    if (busId.includes('STAFF')) return '👔';
    return '📦';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="h6">Failed to Load Bus Registry</Typography>
          <Typography variant="body2">{error}</Typography>
          <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
            Make sure you've run: <code>node scripts/build_frozen_registry.mjs && ./scripts/sync_registry_to_frontend.sh</code>
          </Typography>
        </Alert>
        <Button variant="contained" onClick={loadRegistry} startIcon={<Refresh />}>
          Retry
        </Button>
      </Box>
    );
  }

  if (!registry || !registry.buses) {
    return (
      <Alert severity="warning">
        No registry data available.
      </Alert>
    );
  }

  const busEntries = Object.entries(registry.buses);

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          🚌 Workload Runtime Console (Bus View)
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          Phase-A.2: Bus-grouped workload registry. Capability domains with power state.
        </Typography>
        <Stack direction="row" spacing={2} alignItems="center">
          <Chip label={`Registry v${registry.version}`} size="small" />
          <Chip 
            label={`Generated: ${new Date(registry.generated_at).toLocaleString()}`} 
            size="small" 
            variant="outlined"
          />
          <Button 
            size="small" 
            startIcon={<Refresh />} 
            onClick={loadRegistry}
          >
            Reload
          </Button>
        </Stack>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ borderLeft: '4px solid #4C6EF5', borderRadius: 0 }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                Total Buses
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 700, fontFamily: 'monospace' }}>
                {registry.scan_summary.total_buses}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                Capability domains
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ borderLeft: '4px solid #4C6EF5', borderRadius: 0 }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                Total Workloads
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 700, fontFamily: 'monospace' }}>
                {registry.scan_summary.total_workloads}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                Frozen modules
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ borderLeft: '4px solid #22C55E', borderRadius: 0 }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                Buses ON
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 700, fontFamily: 'monospace' }}>
                {Object.values(busStates).filter(s => s === 'ON').length || '—'}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                Live from kernel API
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Bus Table */}
      <Paper sx={{ mb: 3, borderRadius: 0, borderLeft: '4px solid #4C6EF5' }}>
        <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Typography variant="h6" sx={{ fontFamily: 'monospace' }}>Power Buses</Typography>
          <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
            Click on a bus to expand and view workloads
          </Typography>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Bus</TableCell>
                <TableCell sx={{ width: 100 }} align="right">State</TableCell>
                <TableCell sx={{ width: 100 }} align="right">Workloads</TableCell>
                <TableCell sx={{ width: 120 }} align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {busEntries.map(([busId, busData]) => {
                const liveState = busStates[busId] ?? busData.state;
                const isOn = liveState === 'ON';
                const isLocked = busId === 'KERNEL_CORE_BUS';
                const isToggling = togglingBus === busId;

                return (
                  <TableRow
                    key={busId}
                    sx={{
                      cursor: 'pointer',
                      '&:hover': { bgcolor: 'action.selected' },
                    }}
                    onClick={() => toggleBusExpansion(busId)}
                  >
                    <TableCell>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Typography variant="body2" sx={{ fontSize: '1.5rem' }}>
                          {getBusIcon(busId)}
                        </Typography>
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600, fontFamily: 'monospace' }}>
                            {getBusDisplayName(busId)}
                          </Typography>
                        </Box>
                      </Stack>
                    </TableCell>
                    <TableCell sx={{ width: 100 }} align="right">
                      <Typography
                        variant="body2"
                        sx={{
                          color: isOn ? '#22C55E' : '#9CA3AF',
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                        }}
                      >
                        {liveState}
                      </Typography>
                    </TableCell>
                    <TableCell sx={{ width: 100 }} align="right">
                      <Typography
                        variant="body2"
                        sx={{ color: 'text.secondary', fontFamily: 'monospace', fontSize: '0.75rem' }}
                      >
                        {busData.workloads.length}
                      </Typography>
                    </TableCell>
                    <TableCell sx={{ width: 140 }} align="right" onClick={(e) => e.stopPropagation()}>
                      <Stack direction="row" spacing={1} justifyContent="flex-end" alignItems="center">
                        {isOn && BUS_CONSOLE_ROUTES[busId] && (
                          <Tooltip title={BUS_CONSOLE_ROUTES[busId].tooltip}>
                            <IconButton
                              size="small"
                              onClick={() => navigate(BUS_CONSOLE_ROUTES[busId].path)}
                              sx={{
                                border: `1px solid ${BUS_CONSOLE_ROUTES[busId].color}`,
                                borderRadius: 0,
                                '&:hover': { bgcolor: `${BUS_CONSOLE_ROUTES[busId].color}10` },
                              }}
                            >
                              <Rocket sx={{ fontSize: '1rem', color: BUS_CONSOLE_ROUTES[busId].color }} />
                            </IconButton>
                          </Tooltip>
                        )}
                        {isToggling ? (
                          <CircularProgress size={20} />
                        ) : (
                          <Tooltip title={isLocked ? 'Kernel Core cannot be turned off' : (isOn ? 'Turn OFF' : 'Turn ON')}>
                            <span>
                              <Switch
                                size="small"
                                checked={isOn}
                                disabled={isLocked}
                                onChange={() => toggleBusPower(busId, liveState)}
                                color="success"
                              />
                            </span>
                          </Tooltip>
                        )}
                        <Tooltip title={expandedBuses.has(busId) ? 'Collapse' : 'Expand workloads'}>
                          <IconButton size="small">
                            <ExpandMore
                              sx={{
                                transform: expandedBuses.has(busId) ? 'rotate(180deg)' : 'rotate(0deg)',
                                transition: 'transform 0.3s',
                              }}
                            />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Detailed Bus Workloads */}
      <Typography variant="h6" sx={{ mb: 2 }}>
        Bus Details
      </Typography>
      {busEntries.map(([busId, busData]) => {
        const liveState = busStates[busId] ?? busData.state;
        const isOn = liveState === 'ON';
        return (
        <Accordion
          key={busId}
          sx={{
            mb: 1,
            borderLeft: isOn ? '4px solid #22C55E' : '4px solid #9CA3AF',
            borderRadius: 0,
            '&:before': { display: 'none' },
          }}
          expanded={expandedBuses.has(busId)}
          onChange={() => toggleBusExpansion(busId)}
        >
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
              <Typography variant="h6" sx={{ fontSize: '1.5rem' }}>
                {getBusIcon(busId)}
              </Typography>
              <Typography variant="body1" sx={{ fontWeight: 600, fontFamily: 'monospace' }}>
                {getBusDisplayName(busId)}
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary', ml: 2 }}>
                {busData.workloads.length} workloads
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  color: isOn ? '#22C55E' : '#9CA3AF',
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  ml: 2,
                }}
              >
                {liveState}
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ bgcolor: '#FAFAFA' }}>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Workload</TableCell>
                    <TableCell sx={{ width: 100 }}>Kind</TableCell>
                    <TableCell sx={{ width: 100 }}>World</TableCell>
                    <TableCell sx={{ width: 100 }} align="right">Status</TableCell>
                    <TableCell sx={{ width: 80 }} align="right">Signals</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {busData.workloads.map((workload) => (
                    <TableRow key={workload.name}>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 600, fontFamily: 'monospace', fontSize: '0.875rem' }}>
                          {workload.name}
                        </Typography>
                      </TableCell>
                      <TableCell sx={{ width: 100 }}>
                        <Typography variant="body2" sx={{ color: 'text.secondary', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                          {workload.kind}
                        </Typography>
                      </TableCell>
                      <TableCell sx={{ width: 100 }}>
                        <Typography variant="body2" sx={{ color: 'text.secondary', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                          {workload.world}
                        </Typography>
                      </TableCell>
                      <TableCell sx={{ width: 100 }} align="right">
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            color: workload.status === 'ACTIVE' ? '#22C55E' : '#9CA3AF',
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            fontWeight: 600
                          }}
                        >
                          {workload.status}
                        </Typography>
                      </TableCell>
                      <TableCell sx={{ width: 80 }} align="right">
                        <Stack direction="row" spacing={0.5} alignItems="center" justifyContent="flex-end">
                          <Code sx={{ fontSize: '0.875rem', color: 'text.secondary' }} />
                          <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: '0.75rem' }}>
                            {workload.signals.keywords.length}
                          </Typography>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>
        );
      })}

      {/* Footer Note */}
      <Alert severity="info" sx={{ mt: 4 }}>
        <Typography variant="body2">
          <strong>Workload Runtime Console:</strong> Bus power states are live from the kernel API.
          Use the toggle on each bus row to turn capability buses ON or OFF.
          KERNEL_CORE_BUS is always ON and cannot be changed.
        </Typography>
      </Alert>

      {/* Toast */}
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

export default WorkloadRuntimeConsolePage;

