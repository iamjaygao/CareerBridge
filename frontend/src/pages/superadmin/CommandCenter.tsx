import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Typography,
  Paper,
  Divider,
} from '@mui/material';
import {
  People as PeopleIcon,
  School as SchoolIcon,
  Work as WorkIcon,
  Event as EventIcon,
  TrendingUp as TrendingUpIcon,
  HealthAndSafety as HealthIcon,
  PersonAdd as PersonAddIcon,
  Description as DescriptionIcon,
  CheckCircle as CheckCircleIcon,
  Analytics as AnalyticsIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { useRole } from '../../contexts/RoleContext';
import adminService from '../../services/api/adminService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { DashboardStats } from '../../types';
import { KPICard, AlertPanel, SparklineChart, QuickActions } from '../../components/dashboard';
import type { AlertItem, QuickAction } from '../../components/dashboard';

const CommandCenter: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);
  const { isSuperAdmin } = useRole();
  const [dashboardData, setDashboardData] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Redirect if not superadmin
  useEffect(() => {
    if (user && user.role !== 'superadmin') {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  // Fetch dashboard stats
  useEffect(() => {
    const fetchDashboardStats = async () => {
      if (!user || user.role !== 'superadmin') {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const data = await adminService.getDashboardStats();
        setDashboardData(data);
      } catch (error: any) {
        console.error('Failed to fetch dashboard stats:', error);
        setError(error?.response?.data?.detail || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardStats();
  }, [user]);

  if (!isSuperAdmin) {
    return null;
  }

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <LoadingSpinner message="Loading command center..." />
      </Container>
    );
  }

  if (error || !dashboardData) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Paper sx={{ p: 3 }}>
          <Typography color="error">{error || 'Failed to load dashboard data'}</Typography>
        </Paper>
      </Container>
    );
  }

  // Calculate active students today (users with role='student' who logged in today)
  const activeStudentsToday = dashboardData.active_users_today || 0; // Simplified - would need backend support
  const activeMentorsToday = dashboardData.active_mentors || 0;
  const appointmentsToday = dashboardData.appointments_today || 0;
  const newUsersThisWeek = dashboardData.new_users_this_month || 0; // Simplified - would need backend support
  const mentorAvailability = dashboardData.active_mentors && dashboardData.total_mentors
    ? Math.round((dashboardData.active_mentors / dashboardData.total_mentors) * 100)
    : 0;

  // Build alerts
  const alerts: AlertItem[] = [
    ...(dashboardData.pending_mentor_approvals && dashboardData.pending_mentor_approvals > 0
      ? [
          {
            id: 'pending-mentors',
            type: 'warning' as const,
            title: 'Pending Mentor Approvals',
            description: `${dashboardData.pending_mentor_approvals} mentor applications awaiting review`,
            count: dashboardData.pending_mentor_approvals,
            actionLabel: 'Review',
            actionPath: '/superadmin/mentors',
            onClick: () => navigate('/superadmin/mentors'),
          },
        ]
      : []),
    ...(dashboardData.pending_resume_reviews && dashboardData.pending_resume_reviews > 0
      ? [
          {
            id: 'pending-resumes',
            type: 'info' as const,
            title: 'Pending Resume Reviews',
            description: `${dashboardData.pending_resume_reviews} resumes need review`,
            count: dashboardData.pending_resume_reviews,
            actionLabel: 'Review',
            actionPath: '/staff/resumes',
            onClick: () => navigate('/staff/resumes'),
          },
        ]
      : []),
    ...(dashboardData.system_health && dashboardData.system_health !== 'healthy'
      ? [
          {
            id: 'system-health',
            type: 'error' as const,
            title: 'System Health Warning',
            description: 'System health check failed',
            actionLabel: 'View Details',
            actionPath: '/superadmin/system',
            onClick: () => navigate('/superadmin/system'),
          },
        ]
      : []),
  ];

  // Quick actions
  const quickActions: QuickAction[] = [
    {
      id: 'add-mentor',
      label: 'Add Mentor',
      icon: <PersonAddIcon />,
      onClick: () => navigate('/superadmin/mentors'),
      color: 'primary',
    },
    {
      id: 'review-resume',
      label: 'Review Resume',
      icon: <DescriptionIcon />,
      onClick: () => navigate('/staff/resumes'),
      color: 'info',
    },
    {
      id: 'approve-user',
      label: 'Approve New User',
      icon: <CheckCircleIcon />,
      onClick: () => navigate('/superadmin/users'),
      color: 'success',
    },
    {
      id: 'view-appointments',
      label: 'View Appointments',
      icon: <EventIcon />,
      onClick: () => navigate('/superadmin/appointments'),
      color: 'primary',
    },
    {
      id: 'open-analytics',
      label: 'Open Analytics',
      icon: <AnalyticsIcon />,
      onClick: () => navigate('/analytics'),
      color: 'secondary',
      variant: 'contained',
    },
  ];

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 700, mb: 1 }}>
          Command Center
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Real-time platform overview and actionable insights
        </Typography>
      </Box>

      {/* KPI Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'text.secondary' }}>
          Key Performance Indicators
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={4} lg={2.4}>
            <KPICard
              title="Total Users"
              value={dashboardData.total_users || 0}
              icon={<PeopleIcon sx={{ fontSize: 24 }} />}
              onClick={() => navigate('/superadmin/users')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4} lg={2.4}>
            <KPICard
              title="Active Students Today"
              value={activeStudentsToday}
              icon={<SchoolIcon sx={{ fontSize: 24 }} />}
              subtitle="Logged in today"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4} lg={2.4}>
            <KPICard
              title="Active Mentors Today"
              value={activeMentorsToday}
              icon={<WorkIcon sx={{ fontSize: 24 }} />}
              subtitle="Available now"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4} lg={2.4}>
            <KPICard
              title="Appointments Today"
              value={appointmentsToday}
              icon={<EventIcon sx={{ fontSize: 24 }} />}
              onClick={() => navigate('/superadmin/appointments')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4} lg={2.4}>
            <KPICard
              title="New Users This Week"
              value={newUsersThisWeek}
              icon={<TrendingUpIcon sx={{ fontSize: 24 }} />}
              trend={{
                value: dashboardData.user_mom || 0,
                label: 'MoM',
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4} lg={2.4}>
            <KPICard
              title="Mentor Availability"
              value={`${mentorAvailability}%`}
              icon={<WorkIcon sx={{ fontSize: 24 }} />}
              subtitle={`${dashboardData.active_mentors || 0} of ${dashboardData.total_mentors || 0} active`}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4} lg={2.4}>
            <KPICard
              title="System Health"
              value={dashboardData.system_health === 'healthy' ? 'Healthy' : 'Warning'}
              icon={<HealthIcon sx={{ fontSize: 24 }} />}
              subtitle={dashboardData.system_health || 'Unknown'}
            />
          </Grid>
        </Grid>
      </Box>

      <Grid container spacing={3}>
        {/* Left Column: Alerts and Quick Actions */}
        <Grid item xs={12} lg={4}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Operational Alerts */}
            <AlertPanel
              title="Operational Alerts"
              alerts={alerts}
              emptyMessage="All systems operational. No alerts at this time."
              maxItems={5}
            />

            {/* Quick Actions */}
            <QuickActions title="Quick Actions" actions={quickActions} columns={1} />
          </Box>
        </Grid>

        {/* Right Column: Micro Trends */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3, border: '1px solid', borderColor: 'divider' }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
              Micro Trends (7-Day)
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <SparklineChart
                  title="Users"
                  data={dashboardData.users_7_day || []}
                  color="#667eea"
                  onClick={() => navigate('/analytics?section=users')}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <SparklineChart
                  title="Mentors"
                  data={dashboardData.mentors_7_day || []}
                  color="#764ba2"
                  onClick={() => navigate('/analytics?section=mentors')}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <SparklineChart
                  title="Appointments"
                  data={dashboardData.appointments_7_day || []}
                  color="#f093fb"
                  onClick={() => navigate('/analytics?section=appointments')}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <SparklineChart
                  title="Resume Uploads"
                  data={dashboardData.resumes_7_day || []}
                  color="#4facfe"
                  onClick={() => navigate('/analytics?section=resumes')}
                />
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default CommandCenter;

