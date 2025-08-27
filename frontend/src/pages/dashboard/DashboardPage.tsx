import React, { useEffect, useState } from 'react';
import { Grid, Paper, Typography, Box, Button } from '@mui/material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import { useNavigate } from 'react-router-dom';
import { Description, Event, People, Upload } from '@mui/icons-material';
import dashboardService, { DashboardStats, RecentActivity } from '../../services/api/dashboardService';



const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<DashboardStats>({
    upcomingAppointments: 0,
    resumesUploaded: 0,
    mentorSessions: 0,
    profileViews: 0,
  });
  const [activities, setActivities] = useState<RecentActivity[]>([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const data = await dashboardService.getDashboardData();
        setStats(data.stats);
        setActivities(data.activities);
      } catch (err) {
        setError('Failed to load dashboard data. Please try again later.');
        console.error('Dashboard data fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  const statsData = [
    { title: 'Upcoming Appointments', value: stats.upcomingAppointments, icon: <Event /> },
    { title: 'Resumes Uploaded', value: stats.resumesUploaded, icon: <Description /> },
    { title: 'Mentor Sessions', value: stats.mentorSessions, icon: <People /> },
    { title: 'Profile Views', value: stats.profileViews, icon: <Upload /> },
  ];

  return (
    <>
      <PageHeader
        title={`Welcome, ${user?.username}!`}
        breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }]}
      />
      
      <Grid container spacing={3}>
        {statsData.map((stat) => (
          <Grid item xs={12} sm={6} md={3} key={stat.title}>
            <Paper
              sx={{
                p: 3,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                height: '100%',
                cursor: 'pointer',
                transition: 'all 0.3s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 3,
                },
              }}
              onClick={() => {
                switch (stat.title) {
                  case 'Upcoming Appointments':
                    navigate('/appointments');
                    break;
                  case 'Resumes Uploaded':
                    navigate('/resumes');
                    break;
                  case 'Mentor Sessions':
                    navigate('/mentors');
                    break;
                  default:
                    break;
                }
              }}
            >
              <Box sx={{ mb: 2, color: 'primary.main' }}>{stat.icon}</Box>
              <Typography variant="h3" component="div" gutterBottom>
                {stat.value}
              </Typography>
              <Typography variant="subtitle1" color="text.secondary">
                {stat.title}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3} sx={{ mt: 3 }}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            {activities.length > 0 ? (
              <Box sx={{ mt: 2 }}>
                {activities.map((activity) => (
                  <Box
                    key={activity.id}
                    sx={{
                      py: 2,
                      borderBottom: '1px solid',
                      borderColor: 'divider',
                      '&:last-child': {
                        borderBottom: 'none',
                      },
                    }}
                  >
                    <Typography variant="body1">{activity.description}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(activity.timestamp).toLocaleString()}
                    </Typography>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No recent activities to show.
              </Typography>
            )}
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
              <Button
                variant="contained"
                startIcon={<Upload />}
                onClick={() => navigate('/resumes/upload')}
                fullWidth
              >
                Upload Resume
              </Button>
              <Button
                variant="contained"
                startIcon={<Event />}
                onClick={() => navigate('/appointments/create')}
                fullWidth
              >
                Book Appointment
              </Button>
              <Button
                variant="contained"
                startIcon={<People />}
                onClick={() => navigate('/mentors')}
                fullWidth
              >
                Find Mentor
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </>
  );
};

export default DashboardPage; 