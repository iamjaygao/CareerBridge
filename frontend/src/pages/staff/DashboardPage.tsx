import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  People as PeopleIcon,
  School as SchoolIcon,
  Event as EventIcon,
  Article as ArticleIcon,
  Support as SupportIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import adminService from '../../services/api/adminService';
import { useNotification } from '../../components/common/NotificationProvider';

const StatCard: React.FC<{
  title: string;
  value: number | string;
  subtitle?: string;
  icon: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
}> = ({ title, value, subtitle, icon, color = 'primary' }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Box
          sx={{
            p: 1.5,
            borderRadius: 2,
            bgcolor: `${color}.light`,
            color: `${color}.main`,
            mr: 2,
          }}
        >
          {icon}
        </Box>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4" component="div" fontWeight="bold">
            {value}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="caption" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const StaffDashboardPage: React.FC = () => {
  const { showError } = useNotification();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    pendingMentorApprovals: 0,
    todaysAppointments: 0,
    unresolvedTickets: 0,
    contentDrafts: 0,
  });
  const [systemHealth, setSystemHealth] = useState<any>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [dashboardResult, supportResult, contentResult, healthResult] = await Promise.allSettled([
          adminService.getStaffDashboardStats(),
          adminService.getSupportTickets(),
          adminService.getContent(),
          adminService.getSystemHealth(),
        ]);

        const dashboardStats = dashboardResult.status === 'fulfilled' ? dashboardResult.value : null;
        const supportTicketsRaw = supportResult.status === 'fulfilled' ? supportResult.value : [];
        const contentItemsRaw = contentResult.status === 'fulfilled' ? contentResult.value : [];
        const healthData = healthResult.status === 'fulfilled' ? healthResult.value : null;

        const supportTickets = Array.isArray(supportTicketsRaw)
          ? supportTicketsRaw
          : (supportTicketsRaw?.results || []);
        const contentItems = Array.isArray(contentItemsRaw)
          ? contentItemsRaw
          : (contentItemsRaw?.results || []);

        const unresolvedTickets = Array.isArray(supportTickets)
          ? supportTickets.filter((ticket: any) => ['open', 'in_progress'].includes(ticket.status)).length
          : 0;
        const contentDrafts = Array.isArray(contentItems)
          ? contentItems.filter((item: any) => item.status === 'draft').length
          : 0;

        setStats({
          pendingMentorApprovals: dashboardStats?.pending_mentor_approvals || 0,
          todaysAppointments: dashboardStats?.appointments_today || 0,
          unresolvedTickets,
          contentDrafts,
        });
        setSystemHealth(healthData);
      } catch {
        setStats({
          pendingMentorApprovals: 0,
          todaysAppointments: 0,
          unresolvedTickets: 0,
          contentDrafts: 0,
        });
        showError('Failed to load staff dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [showError]);

  const formatHealthStatus = (status?: string) => {
    if (!status) return 'Unknown';
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  const apiResponseTime = systemHealth?.api_response_time;
  const apiLatencyLabel = apiResponseTime ? `${Math.round(apiResponseTime)}ms (avg)` : 'Unavailable';
  const apiLatencyPercent = apiResponseTime ? Math.min(100, Math.max(5, 100 - apiResponseTime / 5)) : 20;

  if (loading) {
    return <LoadingSpinner message="Loading staff dashboard..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Staff Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Overview of operations and pending tasks
        </Typography>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Pending Mentor Approvals"
            value={stats.pendingMentorApprovals}
            subtitle="Requires review"
            icon={<SchoolIcon />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Today's Appointments"
            value={stats.todaysAppointments}
            subtitle="Scheduled sessions"
            icon={<EventIcon />}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Unresolved Tickets"
            value={stats.unresolvedTickets}
            subtitle="User support issues"
            icon={<SupportIcon />}
            color="error"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Content Drafts"
            value={stats.contentDrafts}
            subtitle="Pending review"
            icon={<ArticleIcon />}
            color="secondary"
          />
        </Grid>
      </Grid>

      {/* System Health (Read-only) */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
            System Health (Read-only)
          </Typography>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={4}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Database Status
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CheckCircleIcon
                    sx={{ color: systemHealth?.database_status === 'healthy' ? 'success.main' : 'warning.main', fontSize: 20 }}
                  />
                  <Typography variant="body2" fontWeight="medium">
                    {formatHealthStatus(systemHealth?.database_status)}
                  </Typography>
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Cache Status
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CheckCircleIcon
                    sx={{ color: systemHealth?.cache_status === 'healthy' ? 'success.main' : 'warning.main', fontSize: 20 }}
                  />
                  <Typography variant="body2" fontWeight="medium">
                    {formatHealthStatus(systemHealth?.cache_status)}
                  </Typography>
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  API Response Time
                </Typography>
                <Typography variant="body2" fontWeight="medium">
                  {apiLatencyLabel}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={apiLatencyPercent}
                  color={apiResponseTime ? 'success' : 'warning'}
                  sx={{ mt: 0.5 }}
                />
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
            Quick Actions
          </Typography>
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Staff Permissions:</strong> You can manage mentor approvals, appointments, content, and user support tickets. 
              System settings and billing are restricted to administrators.
            </Typography>
          </Alert>
        </CardContent>
      </Card>
    </Box>
  );
};

export default StaffDashboardPage;
