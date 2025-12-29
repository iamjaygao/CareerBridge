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
  LinearProgress,
  Button,
  Tabs,
  Tab,
} from '@mui/material';
import {
  People as PeopleIcon,
  School as SchoolIcon,
  Event as EventIcon,
  AttachMoney as MoneyIcon,
  Speed as SpeedIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import adminService, { AdminDashboardStats, AdminSystemHealth } from '../../services/api/adminService';
import { DashboardStats, SystemHealth } from '../../types';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import UserManagementPage from './UserManagementPage';
import MentorApplicationsPage from './MentorApplicationsPage';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { hasAdminAccess } from '../../utils/adminPermissions';
import { hasFinancialAccess } from '../../utils/roleHelpers';
import ErrorAlert from '../../components/common/ErrorAlert';
import { handleApiError } from '../../services/utils/errorHandler';
import type { ApiError } from '../../services/utils/errorHandler';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const StatCard: React.FC<{
  title: string;
  value: number | string;
  subtitle?: string;
  icon: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning';
  trend?: { value: number; isPositive: boolean };
}> = ({ title, value, subtitle, icon, color = 'primary', trend }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Box
          sx={{
            p: 1,
            borderRadius: 1,
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
      {trend && (
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Chip
            label={`${trend.isPositive ? '+' : ''}${trend.value}%`}
            size="small"
            color={trend.isPositive ? 'success' : 'error'}
            variant="outlined"
          />
          <Typography variant="caption" sx={{ ml: 1 }}>
            vs last period
          </Typography>
        </Box>
      )}
    </CardContent>
  </Card>
);

const SystemHealthCard: React.FC<{ health: SystemHealth }> = ({ health }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon color="success" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <ErrorIcon color="error" />;
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          System Health
        </Typography>
        
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            {getStatusIcon(health.database_status || health.database || 'unknown')}
            <Typography variant="body2" sx={{ ml: 1 }}>
              Database: {health.database_status || health.database || 'unknown'}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            {getStatusIcon(health.cache_status || health.cache || 'unknown')}
            <Typography variant="body2" sx={{ ml: 1 }}>
              Cache: {health.cache_status}
            </Typography>
          </Box>
        </Box>

        <Typography variant="subtitle2" gutterBottom>
          System Metrics
        </Typography>
        <Box sx={{ mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            CPU Usage: {health.system_metrics?.cpu_usage || 0}%
          </Typography>
          <LinearProgress
            variant="determinate"
            value={health.system_metrics?.cpu_usage || 0}
            color={(health.system_metrics?.cpu_usage || 0) > 80 ? 'error' : 'primary'}
            sx={{ mt: 0.5 }}
          />
        </Box>
        <Box sx={{ mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Memory Usage: {health.system_metrics?.memory_usage || 0}%
          </Typography>
          <LinearProgress
            variant="determinate"
            value={health.system_metrics?.memory_usage || 0}
            color={(health.system_metrics?.memory_usage || 0) > 80 ? 'error' : 'primary'}
            sx={{ mt: 0.5 }}
          />
        </Box>
        <Box sx={{ mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Disk Usage: {health.system_metrics?.disk_usage || 0}%
          </Typography>
          <LinearProgress
            variant="determinate"
            value={health.system_metrics?.disk_usage || 0}
            color={(health.system_metrics?.disk_usage || 0) > 80 ? 'error' : 'primary'}
            sx={{ mt: 0.5 }}
          />
        </Box>
      </CardContent>
    </Card>
  );
};

const AdminDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [dashboardStats, setDashboardStats] = useState<AdminDashboardStats | null>(null);
  const [systemHealth, setSystemHealth] = useState<AdminSystemHealth | null>(null);
  const [aiStats, setAiStats] = useState<any>(null);
  const todayParam = new Date().toISOString().split('T')[0];
  
  // Check if user has admin access (admin or superadmin)
  const canAccessAdmin = hasAdminAccess(user);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [stats, health, assessmentStats] = await Promise.all([
          adminService.getDashboardStats(),
          adminService.getSystemHealth(),
          adminService.getAssessmentStats(),
        ]);
        setDashboardStats(stats);
        setSystemHealth(health);
        setAiStats(assessmentStats);
      } catch (err) {
        setError(handleApiError(err));
        console.error('Dashboard error:', err);
        // Do not set mock data - let error state display
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'manage-users':
        navigate('/admin/users');
        break;
      case 'review-mentors':
        navigate('/admin/mentors');
        break;
      case 'view-appointments':
        navigate('/admin/appointments');
        break;
      default:
        console.warn('Unknown quick action:', action);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading admin dashboard..." />;
  }

  if (error) {
    return (
      <Box>
        <ErrorAlert error={error} overrideMessage="Failed to load dashboard data." />
      </Box>
    );
  }

  return (
    <>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Admin Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Overview of system metrics and activity
        </Typography>
      </Box>

      <Box>
        <Box sx={{ mb: 3 }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Overview" />
            <Tab label="Users" />
            <Tab label="Mentors" />
            {/* System tab removed - only for superadmin */}
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            {/* Key Metrics */}
                         <Grid item xs={12} md={3}>
               <StatCard
                 title="Total Users"
                 value={dashboardStats?.total_users || 0}
                 subtitle={`Active today: ${dashboardStats?.active_users_today || 0}`}
                 icon={<PeopleIcon />}
                 color="primary"
               />
             </Grid>
             <Grid item xs={12} md={3}>
               <StatCard
                 title="Total Mentors"
                 value={dashboardStats?.total_mentors || 0}
                 subtitle={`Active: ${dashboardStats?.active_mentors || 0}`}
                 icon={<SchoolIcon />}
                 color="secondary"
               />
             </Grid>
             <Grid item xs={12} md={3}>
               <StatCard
                 title="Appointments Today"
                 value={dashboardStats?.appointments_today || 0}
                 subtitle={`Completed: ${dashboardStats?.completed_today || 0}`}
                 icon={<EventIcon />}
                 color="success"
               />
             </Grid>
             <Grid item xs={12} md={3}>
               <StatCard
                 title="Revenue Today"
                 value={`$${dashboardStats?.revenue_today || 0}`}
                 subtitle={`Total: $${dashboardStats?.total_revenue || 0}`}
                 icon={<MoneyIcon />}
                 color="warning"
               />
             </Grid>

            {/* System Health */}
            <Grid item xs={12} md={6}>
              {systemHealth && <SystemHealthCard health={systemHealth} />}
            </Grid>

            {/* Performance Metrics */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Performance Metrics
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Average Response Time: {dashboardStats?.avg_response_time !== undefined && dashboardStats?.avg_response_time !== null ? `${dashboardStats.avg_response_time.toFixed(2)}ms` : 'Unknown'}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={dashboardStats?.avg_response_time !== undefined && dashboardStats?.avg_response_time !== null ? Math.min((dashboardStats.avg_response_time) / 10, 100) : 0}
                      color="primary"
                      sx={{ mt: 0.5 }}
                    />
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Error Rate: {dashboardStats?.error_rate !== undefined && dashboardStats?.error_rate !== null ? `${dashboardStats.error_rate.toFixed(2)}%` : 'Unknown'}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={dashboardStats?.error_rate !== undefined && dashboardStats?.error_rate !== null ? dashboardStats.error_rate : 0}
                      color={dashboardStats?.error_rate !== undefined && dashboardStats?.error_rate !== null && dashboardStats.error_rate > 5 ? 'error' : 'primary'}
                      sx={{ mt: 0.5 }}
                    />
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Uptime: {dashboardStats?.uptime_percentage !== undefined && dashboardStats?.uptime_percentage !== null ? `${dashboardStats.uptime_percentage.toFixed(1)}%` : 'Unknown'}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={dashboardStats?.uptime_percentage !== undefined && dashboardStats?.uptime_percentage !== null ? dashboardStats.uptime_percentage : 0}
                      color="success"
                      sx={{ mt: 0.5 }}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>


            {/* AI Usage Stats */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    AI Usage Statistics
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Resume Analyses (This Month)
                    </Typography>
                    <Typography variant="h5" fontWeight="bold">
                      {aiStats?.total_assessments || 0}
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Resumes Analyzed
                    </Typography>
                    <Typography variant="h5" fontWeight="bold">
                      {aiStats?.total_resumes || 0}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      AI Usage Count
                    </Typography>
                    <Typography variant="h5" fontWeight="bold">
                      {aiStats?.ai_usage || 0}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Action Items */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Action Items
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          Pending mentor approvals
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Review new applications
                        </Typography>
                      </Box>
                      <Chip label={dashboardStats?.pending_mentor_approvals || 0} color="warning" size="small" />
                    </Box>
                    <Button
                      variant="outlined"
                      onClick={() => navigate('/admin/mentors?status=pending')}
                      sx={{ justifyContent: 'flex-start' }}
                    >
                      Review mentors
                    </Button>

                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 1 }}>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          Pending resume reviews
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Assessments waiting for review
                        </Typography>
                      </Box>
                      <Chip label={dashboardStats?.pending_resume_reviews || 0} color="info" size="small" />
                    </Box>
                    <Button
                      variant="outlined"
                      onClick={() => navigate('/admin/assessment')}
                      sx={{ justifyContent: 'flex-start' }}
                    >
                      Review assessments
                    </Button>

                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 1 }}>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          Appointments today
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Monitor session flow
                        </Typography>
                      </Box>
                      <Chip label={dashboardStats?.appointments_today || 0} color="success" size="small" />
                    </Box>
                    <Button
                      variant="outlined"
                      onClick={() => navigate(`/admin/appointments?date_from=${todayParam}&date_to=${todayParam}`)}
                      sx={{ justifyContent: 'flex-start' }}
                    >
                      View appointments
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Quick Actions */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Quick Actions
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                    <Button 
                      variant="outlined" 
                      startIcon={<PeopleIcon />}
                      onClick={() => handleQuickAction('manage-users')}
                      fullWidth
                      sx={{ justifyContent: 'flex-start' }}
                    >
                      Manage Users
                    </Button>
                    <Button 
                      variant="outlined" 
                      startIcon={<SchoolIcon />}
                      onClick={() => handleQuickAction('review-mentors')}
                      fullWidth
                      sx={{ justifyContent: 'flex-start' }}
                    >
                      Review Mentors
                    </Button>
                    <Button 
                      variant="outlined" 
                      startIcon={<EventIcon />}
                      onClick={() => handleQuickAction('view-appointments')}
                      fullWidth
                      sx={{ justifyContent: 'flex-start' }}
                    >
                      View Appointments
                    </Button>
                    {/* System Settings button removed - only for superadmin */}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <UserManagementPage />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <MentorApplicationsPage />
        </TabPanel>
        
        {/* System Settings tab removed - only accessible via /superadmin/system */}
      </Box>
    </>
  );
};

export default AdminDashboardPage; 
