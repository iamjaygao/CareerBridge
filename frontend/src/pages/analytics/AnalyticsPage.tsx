import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Typography,
  Paper,
  Tabs,
  Tab,
  Card,
  CardContent,
  Divider,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  School as SchoolIcon,
  Work as WorkIcon,
  Event as EventIcon,
  Description as DescriptionIcon,
  Assessment as AssessmentIcon,
  Speed as SpeedIcon,
  ErrorOutline as ErrorIcon,
  CloudDone as CloudDoneIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { useRole } from '../../contexts/RoleContext';
import adminService from '../../services/api/adminService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { DashboardStats, TrendDataPoint } from '../../types';
import { KPICard, SparklineChart } from '../../components/dashboard';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const AnalyticsPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { user } = useSelector((state: RootState) => state.auth);
  const { isSuperAdmin } = useRole();
  const [dashboardData, setDashboardData] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);

  // Get initial tab from URL params
  useEffect(() => {
    const section = searchParams.get('section');
    const tabMap: Record<string, number> = {
      growth: 0,
      engagement: 1,
      funnel: 2,
      roles: 3,
      system: 4,
    };
    if (section && tabMap[section] !== undefined) {
      setActiveTab(tabMap[section]);
    }
  }, [searchParams]);

  useEffect(() => {
    if (isSuperAdmin && location.pathname === '/analytics') {
      navigate('/superadmin/analytics', { replace: true });
    }
  }, [isSuperAdmin, location.pathname, navigate]);

  // Fetch dashboard stats
  useEffect(() => {
    const fetchDashboardStats = async () => {
      if (!user || (user.role !== 'superadmin' && user.role !== 'admin')) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const data = await adminService.getDashboardStats();
        setDashboardData(data);
      } catch (error: any) {
        console.error('Failed to fetch analytics data:', error);
        setError(error?.response?.data?.detail || 'Failed to load analytics data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardStats();
  }, [user]);

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <LoadingSpinner message="Loading analytics..." />
      </Container>
    );
  }

  if (error || !dashboardData) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Paper sx={{ p: 3 }}>
          <Typography color="error">{error || 'Failed to load analytics data'}</Typography>
        </Paper>
      </Container>
    );
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 700, mb: 1 }}>
          Analytics & Insights
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Detailed metrics, trends, and performance analysis
        </Typography>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 4 }}>
        <Tabs value={activeTab} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
          <Tab label="Growth Metrics" />
          <Tab label="Engagement Metrics" />
          <Tab label="Funnel Analysis" />
          <Tab label="Role Insights" />
          <Tab label="System Analytics" />
        </Tabs>
      </Paper>

      {/* Growth Metrics Tab */}
      <TabPanel value={activeTab} index={0}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
            Monthly Growth Metrics
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <KPICard
                title="New Users This Month"
                value={dashboardData.new_users_this_month || 0}
                icon={<PeopleIcon sx={{ fontSize: 24 }} />}
                trend={{
                  value: dashboardData.user_mom || 0,
                  label: 'MoM',
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <KPICard
                title="New Students This Month"
                value={dashboardData.new_students_this_month || 0}
                icon={<SchoolIcon sx={{ fontSize: 24 }} />}
                trend={{
                  value: dashboardData.student_mom || 0,
                  label: 'MoM',
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <KPICard
                title="New Mentors This Month"
                value={dashboardData.new_mentors_this_month || 0}
                icon={<WorkIcon sx={{ fontSize: 24 }} />}
                trend={{
                  value: dashboardData.mentor_mom || 0,
                  label: 'MoM',
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <KPICard
                title="New Staff This Month"
                value={dashboardData.new_staff_this_month || 0}
                icon={<PeopleIcon sx={{ fontSize: 24 }} />}
                trend={{
                  value: dashboardData.staff_mom || 0,
                  label: 'MoM',
                }}
              />
            </Grid>
          </Grid>
        </Box>

        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
            Year-over-Year Comparison
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                  {dashboardData.user_yoy ? `${dashboardData.user_yoy >= 0 ? '+' : ''}${dashboardData.user_yoy.toFixed(1)}%` : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Users YoY Growth
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                  {dashboardData.student_yoy ? `${dashboardData.student_yoy >= 0 ? '+' : ''}${dashboardData.student_yoy.toFixed(1)}%` : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Students YoY Growth
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                  {dashboardData.mentor_yoy ? `${dashboardData.mentor_yoy >= 0 ? '+' : ''}${dashboardData.mentor_yoy.toFixed(1)}%` : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Mentors YoY Growth
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                  {dashboardData.staff_yoy ? `${dashboardData.staff_yoy >= 0 ? '+' : ''}${dashboardData.staff_yoy.toFixed(1)}%` : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Staff YoY Growth
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      </TabPanel>

      {/* Engagement Metrics Tab */}
      <TabPanel value={activeTab} index={1}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
            Activity Trends
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  Mentor Activity
                </Typography>
                <SparklineChart
                  title="Mentors (7-Day)"
                  data={dashboardData.mentors_7_day || []}
                  color="#764ba2"
                  height={120}
                />
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  Student Activity
                </Typography>
                <SparklineChart
                  title="Students (7-Day)"
                  data={dashboardData.users_7_day || []}
                  color="#667eea"
                  height={120}
                />
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  Resume Uploads
                </Typography>
                <SparklineChart
                  title="Resumes (7-Day)"
                  data={dashboardData.resumes_7_day || []}
                  color="#4facfe"
                  height={120}
                />
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  Appointment Completion
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Card>
                        <CardContent>
                          <Typography variant="h4" sx={{ fontWeight: 700 }}>
                            {dashboardData.completed_today || 0}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Completed Today
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={6}>
                      <Card>
                        <CardContent>
                          <Typography variant="h4" sx={{ fontWeight: 700 }}>
                            {dashboardData.cancellation_rate ? `${dashboardData.cancellation_rate.toFixed(1)}%` : '0%'}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Cancellation Rate
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      </TabPanel>

      {/* Funnel Analysis Tab */}
      <TabPanel value={activeTab} index={2}>
        <Paper sx={{ p: 4 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 4 }}>
            Conversion Funnel
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Funnel Steps */}
            {[
              { label: 'Signup', value: dashboardData.total_users || 0, icon: <PeopleIcon /> },
              { label: 'Resume Upload', value: dashboardData.resumes_uploaded_this_month || 0, icon: <DescriptionIcon /> },
              { label: 'Appointment Scheduled', value: dashboardData.appointments_this_month || 0, icon: <EventIcon /> },
              { label: 'Completed Session', value: dashboardData.completed_today || 0, icon: <CheckCircleIcon /> },
            ].map((step, index, array) => {
              const prevValue = index > 0 ? array[index - 1].value : step.value;
              const conversionRate = prevValue > 0 ? (step.value / prevValue) * 100 : 0;
              return (
                <Box key={step.label}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box sx={{ color: 'primary.main' }}>{step.icon}</Box>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {step.label}
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="h5" sx={{ fontWeight: 700 }}>
                        {step.value.toLocaleString()}
                      </Typography>
                      {index > 0 && (
                        <Typography variant="caption" color="text.secondary">
                          {conversionRate.toFixed(1)}% conversion
                        </Typography>
                      )}
                    </Box>
                  </Box>
                  <Box
                    sx={{
                      height: 40,
                      bgcolor: 'primary.light',
                      borderRadius: 1,
                      width: `${(step.value / (array[0].value || 1)) * 100}%`,
                      transition: 'width 0.3s ease',
                    }}
                  />
                </Box>
              );
            })}
          </Box>
        </Paper>
      </TabPanel>

      {/* Role Insights Tab */}
      <TabPanel value={activeTab} index={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Students Analytics
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Students
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    {dashboardData.total_students || 0}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Active Today
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    {dashboardData.active_users_today || 0}
                  </Typography>
                </Box>
              </Box>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Mentors Analytics
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Mentors
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    {dashboardData.total_mentors || 0}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Active Mentors
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    {dashboardData.active_mentors || 0}
                  </Typography>
                </Box>
              </Box>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Staff Analytics
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Staff
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    {dashboardData.total_staff || 0}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Active Today
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    {dashboardData.active_staff_today || 0}
                  </Typography>
                </Box>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      {/* System Analytics Tab */}
      <TabPanel value={activeTab} index={4}>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <SpeedIcon sx={{ fontSize: 32, color: dashboardData.avg_response_time !== undefined && dashboardData.avg_response_time !== null ? 'primary.main' : 'text.disabled' }} />
                  <Box>
                    <Typography 
                      variant="h4" 
                      sx={{ 
                        fontWeight: 700,
                        color: dashboardData.avg_response_time === undefined || dashboardData.avg_response_time === null ? 'text.disabled' : 'text.primary'
                      }}
                    >
                      {dashboardData.avg_response_time !== undefined && dashboardData.avg_response_time !== null && dashboardData.avg_response_time > 0
                        ? `${dashboardData.avg_response_time.toFixed(2)}ms` 
                        : 'Unavailable'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      API Response Time
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <ErrorIcon sx={{ fontSize: 32, color: dashboardData.error_rate !== undefined && dashboardData.error_rate !== null ? 'error.main' : 'text.disabled' }} />
                  <Box>
                    <Typography 
                      variant="h4" 
                      sx={{ 
                        fontWeight: 700,
                        color: dashboardData.error_rate === undefined || dashboardData.error_rate === null ? 'text.disabled' : 'text.primary'
                      }}
                    >
                      {dashboardData.error_rate !== undefined && dashboardData.error_rate !== null 
                        ? `${dashboardData.error_rate.toFixed(2)}%` 
                        : 'Unknown'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Error Rate
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <CloudDoneIcon sx={{ fontSize: 32, color: dashboardData.uptime_percentage !== undefined && dashboardData.uptime_percentage !== null ? 'success.main' : 'text.disabled' }} />
                  <Box>
                    <Typography 
                      variant="h4" 
                      sx={{ 
                        fontWeight: 700,
                        color: dashboardData.uptime_percentage === undefined || dashboardData.uptime_percentage === null ? 'text.disabled' : 'text.primary'
                      }}
                    >
                      {dashboardData.uptime_percentage !== undefined && dashboardData.uptime_percentage !== null 
                        ? `${dashboardData.uptime_percentage.toFixed(1)}%` 
                        : 'Unknown'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Uptime
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <AssessmentIcon sx={{ 
                    fontSize: 32, 
                    color: dashboardData.system_health === 'healthy' 
                      ? 'success.main' 
                      : dashboardData.system_health === 'error' 
                        ? 'error.main' 
                        : dashboardData.system_health === 'degraded'
                          ? 'warning.main'
                          : 'text.disabled'
                  }} />
                  <Box>
                    <Typography 
                      variant="h4" 
                      sx={{ 
                        fontWeight: 700, 
                        textTransform: 'capitalize',
                        color: dashboardData.system_health ? 'text.primary' : 'text.disabled'
                      }}
                    >
                      {dashboardData.system_health || 'Unknown'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      System Health
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>
    </Container>
  );
};

export default AnalyticsPage;
