import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  Divider,
  Alert,
  Chip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  School as SchoolIcon,
  Work as WorkIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Settings as SettingsIcon,
  Event as EventIcon,
  AdminPanelSettings as AdminIcon,
  Badge as StaffIcon,
  ArrowUpward,
  ArrowDownward,
  Remove,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { useRole } from '../../contexts/RoleContext';
import adminService from '../../services/api/adminService';
import FinancialOverview from '../../components/admin/FinancialOverview';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { DashboardStats, TrendDataPoint } from '../../types';

const SuperAdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);
  const { isSuperAdmin } = useRole();
  const [dashboardData, setDashboardData] = useState<DashboardStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  // Redirect if not superadmin
  useEffect(() => {
    if (user && user.role !== 'superadmin') {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  // Fetch dashboard stats from backend
  useEffect(() => {
    const fetchDashboardStats = async () => {
      if (!user || (user.role !== 'superadmin' && user.role !== 'admin')) {
        setStatsLoading(false);
        return;
      }

      try {
        setStatsLoading(true);
        setStatsError(null);
        const data = await adminService.getDashboardStats();
        setDashboardData(data);
      } catch (error: any) {
        console.error('Failed to fetch dashboard stats:', error);
        const errorMessage = error?.response?.data?.detail 
          || error?.response?.data?.error
          || error?.message 
          || 'Failed to load dashboard stats';
        setStatsError(errorMessage);
      } finally {
        setStatsLoading(false);
      }
    };

    fetchDashboardStats();
  }, [user]);

  // Helper function to render growth indicator
  const renderGrowthIndicator = (value: number | null | undefined) => {
    if (value === null || value === undefined) {
      return <Remove sx={{ fontSize: 16, color: 'text.secondary' }} />;
    }
    if (value > 0) {
      return <ArrowUpward sx={{ fontSize: 16, color: 'success.main' }} />;
    } else if (value < 0) {
      return <ArrowDownward sx={{ fontSize: 16, color: 'error.main' }} />;
    }
    return <Remove sx={{ fontSize: 16, color: 'text.secondary' }} />;
  };

  // Helper function to format percentage
  const formatPercentage = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return 'N/A';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(1)}%`;
  };

  // Helper function to render metric card with growth
  const renderMetricCard = (
    title: string,
    value: number | string,
    icon: React.ReactNode,
    color: string,
    mom?: number | null,
    yoy?: number | null,
    subtitle?: string
  ) => (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box sx={{ color, mr: 2 }}>{icon}</Box>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h4" component="div">
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
        {(mom !== undefined || yoy !== undefined) && (
          <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
            {mom !== undefined && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {renderGrowthIndicator(mom)}
                <Typography variant="caption" color="text.secondary">
                  MoM: {formatPercentage(mom)}
                </Typography>
              </Box>
            )}
            {yoy !== undefined && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {renderGrowthIndicator(yoy)}
                <Typography variant="caption" color="text.secondary">
                  YoY: {formatPercentage(yoy)}
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );

  // Helper function to render trend chart placeholder
  const renderTrendChart = (title: string, data: TrendDataPoint[] | undefined, color: string) => {
    if (!data || data.length === 0) {
      return (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>{title}</Typography>
            <Typography variant="body2" color="text.secondary">
              No data available
            </Typography>
          </CardContent>
        </Card>
      );
    }

    // Simple bar chart representation
    const maxValue = Math.max(...data.map(d => d.value), 1);
    
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>{title}</Typography>
          <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 1, height: 150, mt: 2 }}>
            {data.map((point, index) => (
              <Box
                key={index}
                sx={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  height: '100%',
                }}
              >
                <Box
                  sx={{
                    width: '100%',
                    bgcolor: color,
                    height: `${(point.value / maxValue) * 100}%`,
                    minHeight: point.value > 0 ? '4px' : 0,
                    borderRadius: '4px 4px 0 0',
                    transition: 'height 0.3s',
                  }}
                />
                <Typography variant="caption" sx={{ mt: 0.5, fontSize: '0.65rem' }}>
                  {new Date(point.date).getDate()}
                </Typography>
              </Box>
            ))}
          </Box>
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="caption" color="text.secondary">
              Total: {data.reduce((sum, d) => sum + d.value, 0)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Avg: {(data.reduce((sum, d) => sum + d.value, 0) / data.length).toFixed(1)}
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  };

  const quickActions = [
    {
      title: 'Users',
      description: 'Manage all users, roles, and permissions',
      icon: <PeopleIcon sx={{ fontSize: 40 }} />,
      path: '/superadmin/users',
      color: '#667eea',
    },
    {
      title: 'Mentors',
      description: 'View and manage all mentors',
      icon: <WorkIcon sx={{ fontSize: 40 }} />,
      path: '/superadmin/mentors',
      color: '#764ba2',
    },
    {
      title: 'Appointments',
      description: 'View and manage all appointments',
      icon: <EventIcon sx={{ fontSize: 40 }} />,
      path: '/superadmin/appointments',
      color: '#f093fb',
    },
    {
      title: 'Assessment Engine',
      description: 'Manage AI assessment system',
      icon: <AssessmentIcon sx={{ fontSize: 40 }} />,
      path: '/superadmin/assessment',
      color: '#4facfe',
    },
    {
      title: 'Market Intelligence',
      description: 'Manage job crawler and market data',
      icon: <TrendingUpIcon sx={{ fontSize: 40 }} />,
      path: '/superadmin/jobs',
      color: '#43e97b',
    },
    {
      title: 'System Console',
      description: 'System logs, config, and health',
      icon: <SettingsIcon sx={{ fontSize: 40 }} />,
      path: '/superadmin/system',
      color: '#ff6b6b',
    },
  ];

  if (!isSuperAdmin) {
    return null;
  }

  if (statsLoading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <LoadingSpinner message="Loading dashboard data..." />
      </Container>
    );
  }

  if (statsError) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error">{statsError}</Alert>
      </Container>
    );
  }

  if (!dashboardData) {
    return null;
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
          Super Admin Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          System overview and management controls
        </Typography>
      </Box>

      {/* SECTION 1: Platform Overview */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" component="h2" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
          Platform Overview
        </Typography>
        <Divider sx={{ mb: 3 }} />
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={2.4}>
            {renderMetricCard(
              'Total Users',
              dashboardData.total_users || 0,
              <PeopleIcon sx={{ fontSize: 40 }} />,
              'primary.main'
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            {renderMetricCard(
              'Students',
              dashboardData.total_students || 0,
              <SchoolIcon sx={{ fontSize: 40 }} />,
              'info.main'
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            {renderMetricCard(
              'Mentors',
              dashboardData.total_mentors || 0,
              <WorkIcon sx={{ fontSize: 40 }} />,
              'success.main'
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            {renderMetricCard(
              'Admins',
              dashboardData.total_admins || 0,
              <AdminIcon sx={{ fontSize: 40 }} />,
              'warning.main'
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            {renderMetricCard(
              'Staff',
              dashboardData.total_staff || 0,
              <StaffIcon sx={{ fontSize: 40 }} />,
              'secondary.main'
            )}
          </Grid>
        </Grid>
      </Paper>

      {/* SECTION 2: Monthly Metrics with MoM & YoY */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" component="h2" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
          Monthly Metrics
        </Typography>
        <Divider sx={{ mb: 3 }} />
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            {renderMetricCard(
              'New Users This Month',
              dashboardData.new_users_this_month || 0,
              <PeopleIcon sx={{ fontSize: 40 }} />,
              'primary.main',
              dashboardData.user_mom,
              dashboardData.user_yoy
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            {renderMetricCard(
              'New Students This Month',
              dashboardData.new_students_this_month || 0,
              <SchoolIcon sx={{ fontSize: 40 }} />,
              'info.main',
              dashboardData.student_mom,
              dashboardData.student_yoy
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            {renderMetricCard(
              'New Mentors This Month',
              dashboardData.new_mentors_this_month || 0,
              <WorkIcon sx={{ fontSize: 40 }} />,
              'success.main',
              dashboardData.mentor_mom,
              dashboardData.mentor_yoy
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            {renderMetricCard(
              'New Staff This Month',
              dashboardData.new_staff_this_month || 0,
              <StaffIcon sx={{ fontSize: 40 }} />,
              'secondary.main',
              dashboardData.staff_mom,
              dashboardData.staff_yoy
            )}
          </Grid>
        </Grid>
      </Paper>

      {/* SECTION 3: Appointment Metrics */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" component="h2" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
          Appointment Metrics
        </Typography>
        <Divider sx={{ mb: 3 }} />
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={4}>
            {renderMetricCard(
              'Appointments This Month',
              dashboardData.appointments_this_month || 0,
              <EventIcon sx={{ fontSize: 40 }} />,
              'warning.main',
              dashboardData.appointment_mom,
              dashboardData.appointment_yoy
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            {renderMetricCard(
              'Cancellation Rate',
              `${(dashboardData.cancellation_rate || 0).toFixed(1)}%`,
              <EventIcon sx={{ fontSize: 40 }} />,
              'error.main'
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            {renderMetricCard(
              'Resumes Uploaded This Month',
              dashboardData.resumes_uploaded_this_month || 0,
              <AssessmentIcon sx={{ fontSize: 40 }} />,
              'info.main',
              dashboardData.resume_mom,
              dashboardData.resume_yoy
            )}
          </Grid>
        </Grid>
      </Paper>

      {/* SECTION 4: Trend Charts (7-Day) */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" component="h2" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
          Trend Analysis (Last 7 Days)
        </Typography>
        <Divider sx={{ mb: 3 }} />
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            {renderTrendChart('Users', dashboardData.users_7_day, '#667eea')}
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            {renderTrendChart('Mentors', dashboardData.mentors_7_day, '#764ba2')}
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            {renderTrendChart('Appointments', dashboardData.appointments_7_day, '#f093fb')}
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            {renderTrendChart('Resumes', dashboardData.resumes_7_day, '#4facfe')}
          </Grid>
        </Grid>
      </Paper>

      {/* SECTION 5: Operational Warnings */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" component="h2" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
          Operational Status
        </Typography>
        <Divider sx={{ mb: 3 }} />
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: (dashboardData.pending_mentor_approvals || 0) > 0 ? 'warning.light' : 'transparent' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <WorkIcon sx={{ fontSize: 32, color: 'warning.main', mr: 2 }} />
                  <Box>
                    <Typography variant="h4">{dashboardData.pending_mentor_approvals || 0}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Pending Mentor Approvals
                    </Typography>
                  </Box>
                </Box>
                {(dashboardData.pending_mentor_approvals || 0) > 0 && (
                  <Chip label="Action Required" color="warning" size="small" />
                )}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: (dashboardData.pending_resume_reviews || 0) > 0 ? 'info.light' : 'transparent' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <AssessmentIcon sx={{ fontSize: 32, color: 'info.main', mr: 2 }} />
                  <Box>
                    <Typography variant="h4">{dashboardData.pending_resume_reviews || 0}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Pending Resume Reviews
                    </Typography>
                  </Box>
                </Box>
                {(dashboardData.pending_resume_reviews || 0) > 0 && (
                  <Chip label="Review Needed" color="info" size="small" />
                )}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            {renderMetricCard(
              'Active Admins Today',
              dashboardData.active_admins_today || 0,
              <AdminIcon sx={{ fontSize: 40 }} />,
              'success.main'
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            {renderMetricCard(
              'Active Staff Today',
              dashboardData.active_staff_today || 0,
              <StaffIcon sx={{ fontSize: 40 }} />,
              'primary.main'
            )}
          </Grid>
        </Grid>
      </Paper>

      {/* Financial Overview Section */}
      {dashboardData.revenue_today !== undefined && (
        <Box sx={{ mb: 4 }}>
          <FinancialOverview
            revenueToday={Number(dashboardData.revenue_today) || 0}
            totalRevenue={Number(dashboardData.total_revenue) || 0}
            mentorEarnings={Number(dashboardData.mentor_earnings) || 0}
            platformEarnings={Number(dashboardData.platform_earnings) || 0}
            pendingPayouts={Number(dashboardData.pending_payouts) || 0}
            revenueTrend={(dashboardData.revenue_trend || []).map((item: any) => ({
              date: item.date,
              amount: item.value || 0,
            }))}
            earningsSplit={
              dashboardData.platform_earnings && dashboardData.mentor_earnings
                ? {
                    platform: Number(dashboardData.platform_earnings),
                    mentor: Number(dashboardData.mentor_earnings),
                  }
                : undefined
            }
          />
        </Box>
      )}

      {/* Quick Actions */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" component="h2" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
          Quick Actions
        </Typography>
        <Divider sx={{ mb: 3 }} />
        <Grid container spacing={3}>
          {quickActions.map((action, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
                onClick={() => navigate(action.path)}
              >
                <CardContent>
                  <Box
                    sx={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      textAlign: 'center',
                    }}
                  >
                    <Box
                      sx={{
                        color: action.color,
                        mb: 2,
                      }}
                    >
                      {action.icon}
                    </Box>
                    <Typography variant="h6" component="h3" gutterBottom>
                      {action.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {action.description}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Role Impersonation Info */}
      <Paper sx={{ p: 3, bgcolor: 'info.light', color: 'info.contrastText' }}>
        <Typography variant="h6" gutterBottom>
          Role Impersonation
        </Typography>
        <Typography variant="body2">
          Use the "Switch Role" menu in your profile dropdown to view the platform from different
          user perspectives. This allows you to test and verify the experience for students, mentors,
          staff, and admins.
        </Typography>
      </Paper>
    </Container>
  );
};

export default SuperAdminDashboard;
