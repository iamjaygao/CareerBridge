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
  Alert,
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
import adminService, { DashboardStats, SystemHealth } from '../../services/api/adminService';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';

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
            {getStatusIcon(health.database_status)}
            <Typography variant="body2" sx={{ ml: 1 }}>
              Database: {health.database_status}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            {getStatusIcon(health.cache_status)}
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
            CPU Usage: {health.system_metrics.cpu_usage}%
          </Typography>
          <LinearProgress
            variant="determinate"
            value={health.system_metrics.cpu_usage}
            color={health.system_metrics.cpu_usage > 80 ? 'error' : 'primary'}
            sx={{ mt: 0.5 }}
          />
        </Box>
        <Box sx={{ mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Memory Usage: {health.system_metrics.memory_usage}%
          </Typography>
          <LinearProgress
            variant="determinate"
            value={health.system_metrics.memory_usage}
            color={health.system_metrics.memory_usage > 80 ? 'error' : 'primary'}
            sx={{ mt: 0.5 }}
          />
        </Box>
        <Box sx={{ mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Disk Usage: {health.system_metrics.disk_usage}%
          </Typography>
          <LinearProgress
            variant="determinate"
            value={health.system_metrics.disk_usage}
            color={health.system_metrics.disk_usage > 80 ? 'error' : 'primary'}
            sx={{ mt: 0.5 }}
          />
        </Box>
      </CardContent>
    </Card>
  );
};

const AdminDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [stats, health] = await Promise.all([
          adminService.getDashboardStats(),
          adminService.getSystemHealth(),
        ]);
        setDashboardStats(stats);
        setSystemHealth(health);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error('Dashboard error:', err);
        // Fallback to mock data for development
        setDashboardStats({
          total_users: 22,
          active_users_today: 5,
          new_users_today: 2,
          total_mentors: 8,
          active_mentors: 6,
          pending_applications: 3,
          total_appointments: 15,
          appointments_today: 3,
          completed_today: 2,
          total_revenue: 1250,
          revenue_today: 150,
          avg_response_time: 250,
          error_rate: 0.5,
          uptime_percentage: 99.8,
        });
        setSystemHealth({
          database_status: 'healthy',
          cache_status: 'healthy',
          external_services: [
            {
              name: 'email_service',
              status: 'healthy',
              response_time: 150,
              last_check: new Date().toISOString(),
            },
            {
              name: 'payment_service',
              status: 'healthy',
              response_time: 200,
              last_check: new Date().toISOString(),
            },
          ],
          system_metrics: {
            cpu_usage: 23.1,
            memory_usage: 67.8,
            disk_usage: 45.2,
            active_connections: 15,
          },
          last_updated: new Date().toISOString(),
        });
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
        navigate('/admin/mentors/applications');
        break;
      case 'view-appointments':
        navigate('/admin/appointments');
        break;
      case 'system-settings':
        navigate('/admin/settings');
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
      <Container>
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <>
      <PageHeader
        title="Admin Dashboard"
        breadcrumbs={[{ label: 'Admin', path: '/admin' }]}
      />

      <Container maxWidth="xl">
        <Box sx={{ mb: 3 }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Overview" />
            <Tab label="Users" />
            <Tab label="Mentors" />
            <Tab label="System" />
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
                 trend={{ value: 12, isPositive: true }}
               />
             </Grid>
             <Grid item xs={12} md={3}>
               <StatCard
                 title="Total Mentors"
                 value={dashboardStats?.total_mentors || 0}
                 subtitle={`Active: ${dashboardStats?.active_mentors || 0}`}
                 icon={<SchoolIcon />}
                 color="secondary"
                 trend={{ value: 8, isPositive: true }}
               />
             </Grid>
             <Grid item xs={12} md={3}>
               <StatCard
                 title="Appointments Today"
                 value={dashboardStats?.appointments_today || 0}
                 subtitle={`Completed: ${dashboardStats?.completed_today || 0}`}
                 icon={<EventIcon />}
                 color="success"
                 trend={{ value: 15, isPositive: true }}
               />
             </Grid>
             <Grid item xs={12} md={3}>
               <StatCard
                 title="Revenue Today"
                 value={`$${dashboardStats?.revenue_today || 0}`}
                 subtitle={`Total: $${dashboardStats?.total_revenue || 0}`}
                 icon={<MoneyIcon />}
                 color="warning"
                 trend={{ value: 5, isPositive: true }}
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
                      Average Response Time: {dashboardStats?.avg_response_time || 0}ms
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min((dashboardStats?.avg_response_time || 0) / 10, 100)}
                      color="primary"
                      sx={{ mt: 0.5 }}
                    />
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Error Rate: {(dashboardStats?.error_rate || 0).toFixed(2)}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={dashboardStats?.error_rate || 0}
                      color={dashboardStats?.error_rate && dashboardStats.error_rate > 5 ? 'error' : 'primary'}
                      sx={{ mt: 0.5 }}
                    />
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Uptime: {dashboardStats?.uptime_percentage || 100}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={dashboardStats?.uptime_percentage || 100}
                      color="success"
                      sx={{ mt: 0.5 }}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Quick Actions */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Quick Actions
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <Button 
                      variant="outlined" 
                      startIcon={<PeopleIcon />}
                      onClick={() => handleQuickAction('manage-users')}
                    >
                      Manage Users
                    </Button>
                    <Button 
                      variant="outlined" 
                      startIcon={<SchoolIcon />}
                      onClick={() => handleQuickAction('review-mentors')}
                    >
                      Review Mentor Applications
                    </Button>
                    <Button 
                      variant="outlined" 
                      startIcon={<EventIcon />}
                      onClick={() => handleQuickAction('view-appointments')}
                    >
                      View All Appointments
                    </Button>
                    <Button 
                      variant="outlined" 
                      startIcon={<SpeedIcon />}
                      onClick={() => handleQuickAction('system-settings')}
                    >
                      System Settings
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6">User Management</Typography>
          <Typography variant="body2" color="text.secondary">
            User management features will be implemented here.
          </Typography>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6">Mentor Management</Typography>
          <Typography variant="body2" color="text.secondary">
            Mentor management features will be implemented here.
          </Typography>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6">System Administration</Typography>
          <Typography variant="body2" color="text.secondary">
            System administration features will be implemented here.
          </Typography>
        </TabPanel>
      </Container>
    </>
  );
};

export default AdminDashboardPage; 