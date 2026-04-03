import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import apiClient from '../../services/api/client';
import {
  Box,
  Container,
  Typography,
  Paper,
  Stack,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Security as SecurityIcon,
  OpenInNew,
  ArrowBack,
} from '@mui/icons-material';
import { RootState } from '../../store';

// ── Per-bus static metadata ────────────────────────────────────────────────────

interface BusLink {
  label: string;
  path: string;
  description: string;
}

interface BusMeta {
  label: string;
  icon: string;
  color: string;
  description: string;
  responsibilities: string[];
  links: BusLink[];
}

const BUS_METADATA: Record<string, BusMeta> = {
  AI_BUS: {
    label: 'AI Capability Bus',
    icon: '🤖',
    color: '#9333EA',
    description:
      'Powers all AI-driven features: ATS signals, resume scoring, career intelligence, and GPT-powered gap analysis.',
    responsibilities: [
      'ATS resume signal extraction and scoring',
      'GPT-4o-mini JD match & gap analysis',
      'Career intelligence engine',
      'AI decision slots and arbitration',
    ],
    links: [
      { label: 'Resume Analysis', path: '/resumes', description: 'Upload and analyse resumes with AI' },
      { label: 'AI Intelligence', path: '/intelligence', description: 'Career AI insights dashboard' },
      { label: 'Workload Runtime', path: '/superadmin/workload-runtime', description: 'AI workload registry view' },
    ],
  },
  ADMIN_BUS: {
    label: 'Admin Operations Bus',
    icon: '🔧',
    color: '#F59E0B',
    description:
      'Powers staff and admin operations: user management, content moderation, system configuration, and reporting.',
    responsibilities: [
      'Staff dashboard and operations console',
      'User management and moderation',
      'Content management system (CMS)',
      'Platform export and reporting pipeline',
    ],
    links: [
      { label: 'Admin Dashboard', path: '/admin', description: 'Main admin control panel' },
      { label: 'User Management', path: '/admin/users', description: 'Manage all platform users' },
      { label: 'Staff Dashboard', path: '/staff', description: 'Staff operations view' },
      { label: 'Governance Audit', path: '/superadmin/audit-logs', description: 'Platform governance logs' },
    ],
  },
  PUBLIC_WEB_BUS: {
    label: 'Public Web Bus',
    icon: '🌐',
    color: '#06B6D4',
    description:
      'Powers all public-facing pages: marketing, landing, resources, pricing, and unauthenticated browsing.',
    responsibilities: [
      'Landing and marketing pages',
      'Public mentor directory (unauthenticated)',
      'Pricing, plans, and onboarding flows',
      'Legal pages (terms, privacy)',
      'Career resource library',
    ],
    links: [
      { label: 'Landing Page', path: '/', description: 'Public homepage' },
      { label: 'Mentors', path: '/mentors', description: 'Public mentor directory' },
      { label: 'Pricing', path: '/pricing', description: 'Plans and pricing page' },
      { label: 'Resources', path: '/resources', description: 'Career resource library' },
      { label: 'About', path: '/about', description: 'About CareerBridge' },
    ],
  },
  MENTOR_BUS: {
    label: 'Mentor / Human-Loop Bus',
    icon: '👥',
    color: '#EC4899',
    description:
      'Powers the mentor ecosystem: scheduling, availability, appointment booking, and the mentor application pipeline.',
    responsibilities: [
      'Mentor availability and calendar management',
      'Appointment booking, rescheduling, and cancellation',
      'Mentor application and approval pipeline',
      'Mentor earnings, feedback, and resources',
    ],
    links: [
      { label: 'Mentor Directory', path: '/mentors', description: 'Browse available mentors' },
      { label: 'Appointments (Admin)', path: '/admin/appointments', description: 'All platform appointments' },
      { label: 'Mentor Approvals', path: '/staff/mentors', description: 'Pending mentor applications' },
      { label: 'Become a Mentor', path: '/become-mentor', description: 'Mentor application entry point' },
    ],
  },
  PAYMENT_BUS: {
    label: 'Payment / Transaction Bus',
    icon: '💳',
    color: '#10B981',
    description:
      'Powers all financial operations: Stripe integration, billing, payouts, promotions, and subscription management.',
    responsibilities: [
      'Stripe payment processing and webhooks',
      'Mentor payout management and disbursement',
      'Subscription and billing lifecycle',
      'Promotions and discount code engine',
    ],
    links: [
      { label: 'Payouts', path: '/admin/payouts', description: 'Mentor payout management' },
      { label: 'Promotions', path: '/admin/promotions', description: 'Discount and promo codes' },
      { label: 'Payment Demo', path: '/payments/demo', description: 'Test payment flows' },
    ],
  },
  SEARCH_BUS: {
    label: 'Search / Discovery Bus',
    icon: '🔍',
    color: '#F97316',
    description:
      'Powers search, filtering, and analytics: mentor discovery, platform-wide analytics, and data export pipelines.',
    responsibilities: [
      'Mentor search, filtering, and ranking',
      'Platform-wide analytics and reporting',
      'Data export pipelines',
      'Discovery and recommendation engine',
    ],
    links: [
      { label: 'Mentor Search', path: '/mentors', description: 'Search and discover mentors' },
      { label: 'Analytics', path: '/analytics', description: 'Platform analytics dashboard' },
      { label: 'Admin Exports', path: '/admin/exports', description: 'Data export management' },
    ],
  },
};

// ── Types ──────────────────────────────────────────────────────────────────────

interface BusState {
  bus_name: string;
  state: 'ON' | 'OFF';
  reason: string;
  updated_at: string | null;
}

interface Workload {
  name: string;
  kind: string;
  world: string;
  status: string;
  reason: string;
}

interface Registry {
  buses: Record<string, { state: 'ON' | 'OFF'; workloads: Workload[] }>;
}

// ── Component ──────────────────────────────────────────────────────────────────

const BusConsolePage: React.FC = () => {
  const { busId } = useParams<{ busId: string }>();
  const navigate = useNavigate();
  const { token } = useSelector((state: RootState) => state.auth);

  const [busState, setBusState] = useState<BusState | null>(null);
  const [workloads, setWorkloads] = useState<Workload[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const meta = busId ? BUS_METADATA[busId] : null;

  useEffect(() => {
    if (!busId || !meta) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [busRes, regRes] = await Promise.all([
          apiClient.get('/kernel/console/buses/'),
          fetch('/registry/WORKLOAD_FROZEN_BUS_REGISTRY.json'),
        ]);

        const found: BusState = busRes.data.find((b: BusState) => b.bus_name === busId) ?? null;
        setBusState(found);

        if (regRes.ok) {
          const reg: Registry = await regRes.json();
          setWorkloads(reg.buses[busId]?.workloads ?? []);
        }
      } catch (e: any) {
        setError(e?.response?.data?.detail || e?.message || 'Failed to load bus data');
      } finally {
        setLoading(false);
      }
    };

    load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busId]);

  if (!meta || !busId) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">Unknown bus: {busId}</Alert>
      </Container>
    );
  }

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  const isOn = busState?.state === 'ON';

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>

      <Alert severity="warning" icon={<SecurityIcon />} sx={{ mb: 4, fontWeight: 600 }}>
        ⚠️ You are operating the CareerBridge OS Kernel. All actions are audited.
      </Alert>

      {/* Back + Header */}
      <Box sx={{ mb: 1 }}>
        <Button
          size="small"
          startIcon={<ArrowBack />}
          onClick={() => navigate('/superadmin/workload-runtime')}
          sx={{ mb: 2, fontFamily: 'monospace', fontSize: '0.75rem' }}
        >
          Workload Runtime Console
        </Button>
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 0.5 }}>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            {meta.icon} {meta.label}
          </Typography>
          <Chip
            label={busState?.state ?? 'UNKNOWN'}
            size="small"
            sx={{
              bgcolor: isOn ? 'success.main' : 'error.main',
              color: 'white',
              fontWeight: 700,
              fontFamily: 'monospace',
            }}
          />
        </Stack>
        <Typography variant="body2" color="text.secondary">
          {meta.description}
        </Typography>
      </Box>

      <Divider sx={{ my: 3 }} />

      <Stack spacing={3}>

        {/* ── Bus State ── */}
        <Paper sx={{ p: 3, borderRadius: 0, borderLeft: `4px solid ${isOn ? '#22C55E' : '#9CA3AF'}` }}>
          <Typography variant="h6" sx={{ mb: 2, fontFamily: 'monospace' }}>Bus State</Typography>
          <Stack direction="row" spacing={4} flexWrap="wrap">
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>BUS</Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>{busId}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>STATE</Typography>
              <Typography
                variant="body2"
                sx={{ fontFamily: 'monospace', fontWeight: 600, color: isOn ? '#22C55E' : '#9CA3AF' }}
              >
                {busState?.state ?? '—'}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>LAST UPDATED</Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                {busState?.updated_at ? new Date(busState.updated_at).toLocaleString() : 'Not set'}
              </Typography>
            </Box>
            {busState?.reason && (
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>REASON</Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{busState.reason}</Typography>
              </Box>
            )}
          </Stack>
        </Paper>

        {/* ── Responsibilities ── */}
        <Paper sx={{ p: 3, borderRadius: 0, borderLeft: `4px solid ${meta.color}` }}>
          <Typography variant="h6" sx={{ mb: 2, fontFamily: 'monospace' }}>Responsibilities</Typography>
          <Stack spacing={0.75}>
            {meta.responsibilities.map((r, i) => (
              <Stack key={i} direction="row" spacing={1} alignItems="flex-start">
                <Typography variant="body2" sx={{ fontFamily: 'monospace', color: meta.color, mt: '1px' }}>▸</Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{r}</Typography>
              </Stack>
            ))}
          </Stack>
        </Paper>

        {/* ── Navigation Links ── */}
        <Paper sx={{ p: 3, borderRadius: 0, borderLeft: '4px solid #4C6EF5' }}>
          <Typography variant="h6" sx={{ mb: 2, fontFamily: 'monospace' }}>Console Links</Typography>
          <Stack spacing={1}>
            {meta.links.map((link, i) => (
              <Stack
                key={i}
                direction="row"
                spacing={2}
                alignItems="center"
                sx={{
                  p: 1.5,
                  border: '1px solid',
                  borderColor: 'divider',
                  cursor: 'pointer',
                  '&:hover': { bgcolor: 'action.hover' },
                }}
                onClick={() => navigate(link.path)}
              >
                <OpenInNew sx={{ fontSize: '1rem', color: 'text.secondary' }} />
                <Box sx={{ flex: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, fontFamily: 'monospace' }}>
                    {link.label}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {link.description}
                  </Typography>
                </Box>
                <Typography variant="caption" sx={{ fontFamily: 'monospace', color: 'text.disabled' }}>
                  {link.path}
                </Typography>
              </Stack>
            ))}
          </Stack>
        </Paper>

        {/* ── Workloads ── */}
        <Paper sx={{ p: 3, borderRadius: 0, borderLeft: '4px solid #9CA3AF' }}>
          <Typography variant="h6" sx={{ mb: 2, fontFamily: 'monospace' }}>
            Registered Workloads ({workloads.length})
          </Typography>
          {workloads.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
              No workloads registered under this bus in the static registry.
            </Typography>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>Workload</TableCell>
                    <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', width: 100 }}>Kind</TableCell>
                    <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', width: 100 }}>World</TableCell>
                    <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', width: 120 }} align="right">Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {workloads.map((w) => (
                    <TableRow key={w.name}>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600, fontSize: '0.875rem' }}>
                          {w.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'text.secondary' }}>
                          {w.kind}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'text.secondary' }}>
                          {w.world}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          sx={{
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            color: w.status === 'ACTIVE' ? '#22C55E' : '#9CA3AF',
                          }}
                        >
                          {w.status}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>

        {/* ── Kernel log footer ── */}
        <Paper sx={{ p: 2.5, borderRadius: 0, borderLeft: `4px solid ${isOn ? '#22C55E' : '#9CA3AF'}`, bgcolor: '#FAFAFA' }}>
          <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', lineHeight: 1.8 }}>
            [KERNEL] Bus: {busId} = <span style={{ color: isOn ? '#22C55E' : '#9CA3AF', fontWeight: 600 }}>{busState?.state ?? 'UNKNOWN'}</span><br />
            [KERNEL] Workloads registered: {workloads.length}<br />
            [KERNEL] Console accessed at: {new Date().toLocaleString()}
          </Typography>
        </Paper>

      </Stack>
    </Container>
  );
};

export default BusConsolePage;
