import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Alert, 
  Chip,
  CircularProgress,
  Stack,
  Paper
} from '@mui/material';
import { 
  Rocket as RocketIcon, 
  Security as SecurityIcon,
  CheckCircle,
  Error as ErrorIcon
} from '@mui/icons-material';
import apiClient from '../../services/api/client';

interface HealthResponse {
  ok: boolean;
  service: string;
  ts: string;
}

interface StatusResponse {
  bus: string;
  state: string;
  ts: string;
}

const PeerMockConsolePage: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);

      try {
        const [healthRes, statusRes, sessionsRes] = await Promise.all([
          apiClient.get('/api/v1/peer-mock/health/'),
          apiClient.get('/api/v1/peer-mock/status/'),
          apiClient.get('/api/v1/peer-mock/sessions/')
        ]);

        setHealth(healthRes.data);
        setStatus(statusRes.data);
        setSessions(sessionsRes.data);
      } catch (err: any) {
        const failedUrl = err.config?.url || 'unknown';
        setError(`Failed to load peer-mock data. URL: ${failedUrl}, Status: ${err.response?.status || 'N/A'}`);
        console.error('Peer mock load error:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error" icon={<ErrorIcon />}>
          <Typography variant="h6">Peer Mock Console Load Failed</Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>{error}</Typography>
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Alert 
        severity="warning" 
        icon={<SecurityIcon />}
        sx={{ mb: 4, fontWeight: 600 }}
      >
        ⚠️ You are operating the CareerBridge OS Kernel. All actions are audited.
      </Alert>

      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Peer Mock Runtime Console
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Phase-B Sprint-0: First unfrozen workload
        </Typography>
      </Box>

      <Stack spacing={3}>
        <Paper sx={{ p: 3, borderRadius: 0, borderLeft: '4px solid #4C6EF5' }}>
          <Typography variant="h6" sx={{ mb: 2, fontFamily: 'monospace' }}>Service Health</Typography>
          <Stack direction="row" spacing={2} alignItems="center">
            {health?.ok ? (
              <>
                <CheckCircle sx={{ color: 'text.secondary' }} />
                <Typography sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                  Service: {health.service}
                </Typography>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    color: '#22C55E',
                    fontFamily: 'monospace',
                    fontSize: '0.75rem',
                    fontWeight: 600
                  }}
                >
                  HEALTHY
                </Typography>
              </>
            ) : (
              <>
                <ErrorIcon sx={{ color: 'text.secondary' }} />
                <Typography 
                  variant="body2" 
                  sx={{ 
                    color: '#9CA3AF',
                    fontFamily: 'monospace',
                    fontSize: '0.75rem',
                    fontWeight: 600
                  }}
                >
                  UNHEALTHY
                </Typography>
              </>
            )}
          </Stack>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            Last check: {health?.ts || 'N/A'}
          </Typography>
        </Paper>

        <Paper sx={{ p: 3, borderRadius: 0, borderLeft: '4px solid #22C55E' }}>
          <Typography variant="h6" sx={{ mb: 2, fontFamily: 'monospace' }}>Bus State</Typography>
          <Stack direction="row" spacing={2} alignItems="center">
            <RocketIcon sx={{ color: 'text.secondary' }} />
            <Typography sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
              Bus: {status?.bus?.replace('_BUS', '') || 'N/A'}
            </Typography>
            <Typography 
              variant="body2" 
              sx={{ 
                color: status?.state === 'ON' ? '#22C55E' : '#9CA3AF',
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                fontWeight: 600
              }}
            >
              {status?.state}
            </Typography>
          </Stack>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            Timestamp: {status?.ts || 'N/A'}
          </Typography>
        </Paper>

        <Paper sx={{ p: 3, borderRadius: 0, borderLeft: '4px solid #9CA3AF' }}>
          <Typography variant="h6" sx={{ mb: 2, fontFamily: 'monospace' }}>Active Sessions</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
            {sessions.length === 0 ? 'No active sessions' : `${sessions.length} session(s)`}
          </Typography>
        </Paper>

        <Card sx={{ borderRadius: 0, borderLeft: '4px solid #22C55E' }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
              [KERNEL] Peer Mock Runtime Online<br />
              [KERNEL] Bus: PEER_MOCK = <span style={{ color: '#22C55E', fontWeight: 600 }}>ON</span><br />
              [KERNEL] Workload: peer-mock<br />
              [KERNEL] Status: <span style={{ color: '#22C55E', fontWeight: 600 }}>ACTIVE</span><br />
              [KERNEL] Phase-B Sprint-0: ✅ COMPLETE
            </Typography>
          </CardContent>
        </Card>
      </Stack>
    </Container>
  );
};

export default PeerMockConsolePage;
