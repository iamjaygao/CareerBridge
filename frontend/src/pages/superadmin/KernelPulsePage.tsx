/**
 * Kernel Pulse Page - Phase-A.1
 * 
 * Read-only kernel observability plane.
 * Shows kernel state reconstruction from audit logs.
 * 
 * Invariants:
 * - ONE XHR on mount: /kernel/pulse/summary/
 * - NO frozen module calls
 * - NO legacy dashboard imports
 * - SuperAdmin world only
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  CircularProgress,
} from '@mui/material';
import apiClient from '../../services/api/client';

interface KernelState {
  mode: 'NORMAL' | 'DEGRADED' | 'LOCKED';
  active_lock_pressure: 'LOW' | 'MEDIUM' | 'HIGH';
  error_rate_1h: number;
  chaos_safe: boolean;
}

interface Syscall {
  at: string;
  syscall: string;
  decision_slot_id: string | null;
  outcome: string;
  error_code: string | null;
  trace_id: string | null;
  resource_type: string | null;
  resource_id: string | null;
  owner_id: string | null;
}

interface Counts {
  total: number;
  success: number;
  retryable: number;
  terminal: number;
  conflict: number;
}

interface Lock {
  resource_type: string;
  resource_id: string;
  owner_id: string | null;
  expires_at: string | null;
  status: string;
}

interface TopError {
  error_code: string;
  count: number;
}

interface PulseData {
  pulse_version: string;
  now: string;
  kernel_state: KernelState;
  recent_syscalls: Syscall[];
  counts: {
    last_1h: Counts;
    last_24h: Counts;
  };
  active_locks: {
    count: number;
    samples: Lock[];
  };
  top_errors_24h: TopError[];
}

const KernelPulsePage: React.FC = () => {
  const [data, setData] = useState<PulseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Phase-A.1: ONE XHR on mount only
    const fetchPulse = async () => {
      try {
        const response = await apiClient.get('/kernel/pulse/summary/');
        setData(response.data);
        setError(null);
      } catch (err: any) {
        if (err.response?.status === 403) {
          setError('Kernel access denied');
        } else {
          setError(err.message || 'Failed to load kernel pulse');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPulse();
  }, []); // No dependencies - runs once on mount only

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!data) {
    return null;
  }

  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'NORMAL': return 'success';
      case 'DEGRADED': return 'warning';
      case 'LOCKED': return 'error';
      default: return 'default';
    }
  };

  const getPressureColor = (pressure: string) => {
    switch (pressure) {
      case 'LOW': return 'success';
      case 'MEDIUM': return 'warning';
      case 'HIGH': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box p={3}>
      {/* Header */}
      <Typography variant="h4" gutterBottom>
        Kernel Pulse
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Phase-A.1 | Read-only observability plane | Pulse ABI v{data.pulse_version}
      </Typography>

      {/* Kernel State */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={3}>
          <Card sx={{ borderRadius: 0, borderLeft: '4px solid #4C6EF5' }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                Kernel Mode
              </Typography>
              <Box mt={1}>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    fontFamily: 'monospace',
                    fontWeight: 600,
                    color: data.kernel_state.mode === 'NORMAL' ? '#22C55E' : data.kernel_state.mode === 'DEGRADED' ? '#F59E0B' : '#9CA3AF'
                  }}
                >
                  {data.kernel_state.mode}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ borderRadius: 0, borderLeft: '4px solid #4C6EF5' }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                Lock Pressure
              </Typography>
              <Box mt={1}>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    fontFamily: 'monospace',
                    fontWeight: 600,
                    color: data.kernel_state.active_lock_pressure === 'LOW' ? '#22C55E' : data.kernel_state.active_lock_pressure === 'MEDIUM' ? '#F59E0B' : '#9CA3AF'
                  }}
                >
                  {data.kernel_state.active_lock_pressure}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ borderRadius: 0, borderLeft: '4px solid #4C6EF5' }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                Error Rate (1h)
              </Typography>
              <Typography variant="h6" mt={1} sx={{ fontFamily: 'monospace' }}>
                {(data.kernel_state.error_rate_1h * 100).toFixed(2)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ borderRadius: 0, borderLeft: data.kernel_state.chaos_safe ? '4px solid #22C55E' : '4px solid #9CA3AF' }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                Chaos Safe
              </Typography>
              <Typography 
                variant="h6" 
                mt={1} 
                sx={{ 
                  fontFamily: 'monospace',
                  color: data.kernel_state.chaos_safe ? '#22C55E' : '#9CA3AF'
                }}
              >
                {data.kernel_state.chaos_safe ? '✅ YES' : '❌ NO'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Counts */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Last 1 Hour
              </Typography>
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell>Total</TableCell>
                    <TableCell align="right">{data.counts.last_1h.total}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Success</TableCell>
                    <TableCell align="right">{data.counts.last_1h.success}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Retryable</TableCell>
                    <TableCell align="right">{data.counts.last_1h.retryable}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Terminal</TableCell>
                    <TableCell align="right">{data.counts.last_1h.terminal}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Conflict</TableCell>
                    <TableCell align="right">{data.counts.last_1h.conflict}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Last 24 Hours
              </Typography>
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell>Total</TableCell>
                    <TableCell align="right">{data.counts.last_24h.total}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Success</TableCell>
                    <TableCell align="right">{data.counts.last_24h.success}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Retryable</TableCell>
                    <TableCell align="right">{data.counts.last_24h.retryable}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Terminal</TableCell>
                    <TableCell align="right">{data.counts.last_24h.terminal}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Conflict</TableCell>
                    <TableCell align="right">{data.counts.last_24h.conflict}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Active Locks */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Active Locks ({data.active_locks.count})
          </Typography>
          <TableContainer component={Paper} sx={{ mt: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Resource Type</TableCell>
                  <TableCell>Resource ID</TableCell>
                  <TableCell>Owner ID</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Expires At</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.active_locks.samples.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      No active locks
                    </TableCell>
                  </TableRow>
                ) : (
                  data.active_locks.samples.map((lock, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{lock.resource_type}</TableCell>
                      <TableCell>{lock.resource_id}</TableCell>
                      <TableCell>{lock.owner_id || 'N/A'}</TableCell>
                      <TableCell>
                        <Chip label={lock.status} size="small" />
                      </TableCell>
                      <TableCell>
                        {lock.expires_at
                          ? new Date(lock.expires_at).toLocaleString()
                          : 'Never'}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Top Errors */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Top Errors (24h)
          </Typography>
          <TableContainer component={Paper} sx={{ mt: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Error Code</TableCell>
                  <TableCell align="right">Count</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.top_errors_24h.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={2} align="center">
                      No errors in last 24h
                    </TableCell>
                  </TableRow>
                ) : (
                  data.top_errors_24h.map((error, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{error.error_code}</TableCell>
                      <TableCell align="right">{error.count}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Recent Syscalls */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Syscalls (Last 20)
          </Typography>
          <TableContainer component={Paper} sx={{ mt: 2, maxHeight: 400 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Time</TableCell>
                  <TableCell>Syscall</TableCell>
                  <TableCell>Outcome</TableCell>
                  <TableCell>Resource</TableCell>
                  <TableCell>Error Code</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.recent_syscalls.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      No recent syscalls
                    </TableCell>
                  </TableRow>
                ) : (
                  data.recent_syscalls.map((syscall, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        {new Date(syscall.at).toLocaleString()}
                      </TableCell>
                      <TableCell>{syscall.syscall}</TableCell>
                      <TableCell>
                        <Chip
                          label={syscall.outcome}
                          size="small"
                          color={syscall.outcome === 'SUCCESS' ? 'success' : 'error'}
                        />
                      </TableCell>
                      <TableCell>
                        {syscall.resource_type
                          ? `${syscall.resource_type}:${syscall.resource_id}`
                          : 'N/A'}
                      </TableCell>
                      <TableCell>{syscall.error_code || '-'}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default KernelPulsePage;
