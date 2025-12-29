import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Grid,
  Box,
  Tabs,
  Tab,
  Button,
  Snackbar,
  Alert,
  TextField,
  MenuItem,
  Typography,
  Pagination,
  Paper,
} from '@mui/material';
import { Add as AddIcon, School as SchoolIcon, CheckCircle as CheckCircleIcon } from '@mui/icons-material';
import { RootState } from '../../store';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import RegistrationBanner from '../../components/common/RegistrationBanner';
import AppointmentCard from '../../components/appointments/AppointmentCard';
import appointmentService from '../../services/api/appointmentService';
import apiClient from '../../services/api/client';
import { Appointment } from '../../types';
import { format } from 'date-fns';

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
      id={`appointment-tabpanel-${index}`}
      aria-labelledby={`appointment-tab-${index}`}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const AppointmentListPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<{ sort_by?: string; status?: string }>({});

  useEffect(() => {
    if (isAuthenticated) {
      fetchAppointments();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    const params = new URLSearchParams(location.search);
    const paymentStatus = params.get('payment');
    const sessionId = params.get('session_id');
    const paymentIntentId = params.get('payment_intent') || params.get('payment_intent_id');

    if (paymentStatus === 'success' && (sessionId || paymentIntentId)) {
      (async () => {
        try {
          await apiClient.post('/payments/reconcile/', {
            session_id: sessionId,
            payment_intent_id: paymentIntentId,
          });
          await fetchAppointments();
        } catch (err: any) {
          console.error('Payment reconcile failed:', err);
        } finally {
          navigate('/student/appointments', { replace: true });
        }
      })();
    }
  }, [isAuthenticated, location.search, navigate]);

  const fetchAppointments = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await appointmentService.getAppointments();
      const data = Array.isArray(response) ? response : ((response as any).results || []);
      
      // Transform backend data to match Appointment interface
      const transformedAppointments: Appointment[] = data.map((apt: any) => {
        const scheduledStart = new Date(apt.scheduled_start);
        const scheduledEnd = new Date(apt.scheduled_end);
        
        return {
          id: apt.id,
          mentor: apt.mentor,
          user: apt.user,
          date: format(scheduledStart, 'yyyy-MM-dd'),
          time: format(scheduledStart, 'HH:mm'),
          status: apt.status,
          notes: apt.description,
          meeting_link: apt.meeting_link,
          meeting_platform: apt.meeting_platform,
          user_feedback: apt.user_feedback,
          mentor_feedback: apt.mentor_feedback,
          user_rating: apt.user_rating,
          scheduled_start: apt.scheduled_start,
          scheduled_end: apt.scheduled_end,
          title: apt.title,
        };
      });
      
      setAppointments(transformedAppointments);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to load appointments');
      console.error('Failed to fetch appointments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleReschedule = (appointmentId: number) => {
    navigate(`/student/appointments/${appointmentId}/reschedule`);
  };

  const handleNewAppointment = () => {
    if (!isAuthenticated) {
      navigate('/login', { state: { redirectTo: '/appointments' } });
      return;
    }
    navigate('/appointments/create');
  };

  const handleSnackbarClose = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const handleCompletePayment = (appointmentId: number) => {
    navigate(`/appointments/${appointmentId}/pay`);
  };

  const guidanceBenefits: string[] = [
    'Schedule one-on-one sessions with expert mentors',
    'Get personalized career advice tailored to your goals',
    'Track your career development progress over time',
    'Access exclusive career resources and materials',
    'Build a network of professional connections',
  ];

  // Classify appointments based on status and scheduled_start time
  const now = new Date();
  const upcomingAppointments = appointments.filter((apt) => {
    if (!apt.scheduled_start) return false;
    const appointmentTime = new Date(apt.scheduled_start);
    return (
      (apt.status === 'pending' || apt.status === 'confirmed') &&
      appointmentTime > now
    );
  });
  
  const pastAppointments = appointments.filter((apt) => {
    if (!apt.scheduled_start) return false;
    const appointmentTime = new Date(apt.scheduled_start);
    const isUpcoming = (apt.status === 'pending' || apt.status === 'confirmed') && appointmentTime > now;
    return !isUpcoming;
  });

  // For unauthenticated users, don't show loading or error states
  // They should see the introduction content
  if (isAuthenticated) {
    if (loading) {
      return <LoadingSpinner message="Loading appointments..." />;
    }

    if (error) {
      return <ErrorAlert message={error} />;
    }
  }

  return (
    <>
      <PageHeader
        title="Career Guidance"
        breadcrumbs={[{ label: 'Appointments', path: '/appointments' }]}
        action={
          isAuthenticated && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleNewAppointment}
            >
              Book Appointment
            </Button>
          )
        }
      />

      {!isAuthenticated && (
        <RegistrationBanner
          title="Start Your Career Journey Today"
          description="Sign up for free to book mentorship sessions, get personalized career guidance, and connect with industry experts."
        />
      )}

      {!isAuthenticated && (
        <Paper sx={{ p: 4, mb: 4, background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <SchoolIcon sx={{ fontSize: 48, color: 'primary.main', mr: 2 }} />
            <Box>
              <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
                Personalized Career Guidance
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Get expert advice and mentorship to advance your career
              </Typography>
            </Box>
          </Box>
          <Grid container spacing={2}>
            {guidanceBenefits.map((benefit, index) => (
              <Grid item xs={12} sm={6} key={index}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                  <CheckCircleIcon sx={{ color: 'success.main', mr: 1, mt: 0.5 }} />
                  <Typography variant="body2">{benefit}</Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {isAuthenticated && (
        <>
          <Box sx={{ mb: 3 }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
              <Tabs value={tabValue} onChange={handleTabChange}>
                <Tab label={`Upcoming (${upcomingAppointments.length})`} />
                <Tab label={`Past (${pastAppointments.length})`} />
              </Tabs>
            </Box>

            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <TextField
                select
                label="Sort by"
                size="small"
                sx={{ width: 200 }}
                value={filters.sort_by || 'date'}
                onChange={(e) =>
                  setFilters({ ...filters, sort_by: e.target.value })
                }
              >
                <MenuItem value="date">Date</MenuItem>
                <MenuItem value="status">Status</MenuItem>
                <MenuItem value="mentor">Mentor Name</MenuItem>
              </TextField>

              {tabValue === 0 && (
                <TextField
                  select
                  label="Status"
                  size="small"
                  sx={{ width: 200 }}
                  value={filters.status || 'all'}
                  onChange={(e) =>
                    setFilters({ ...filters, status: e.target.value })
                  }
                >
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="confirmed">Confirmed</MenuItem>
                </TextField>
              )}
            </Box>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              {upcomingAppointments.length > 0 ? (
                upcomingAppointments.map((appointment) => (
                  <Grid item xs={12} md={6} key={appointment.id}>
                    <AppointmentCard
                      appointment={appointment}
                      onReschedule={handleReschedule}
                      onCompletePayment={handleCompletePayment}
                    />
                  </Grid>
                ))
              ) : (
                <Grid item xs={12}>
                  <Box
                    sx={{
                      textAlign: 'center',
                      py: 8,
                      px: 2,
                      bgcolor: 'background.paper',
                      borderRadius: 1,
                    }}
                  >
                    <Typography variant="h6" gutterBottom>
                      No upcoming appointments
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Book a session with a mentor to get started
                    </Typography>
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={handleNewAppointment}
                      sx={{ mt: 2 }}
                    >
                      Book Appointment
                    </Button>
                  </Box>
                </Grid>
              )}
            </Grid>

            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination page={page} onChange={(_: React.ChangeEvent<unknown>, p: number) => setPage(p)} count={10} color="primary" />
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={3}>
              {pastAppointments.length > 0 ? (
                pastAppointments.map((appointment) => (
                  <Grid item xs={12} md={6} key={appointment.id}>
                    <AppointmentCard appointment={appointment} />
                  </Grid>
                ))
              ) : (
                <Grid item xs={12}>
                  <Box
                    sx={{
                      textAlign: 'center',
                      py: 8,
                      px: 2,
                      bgcolor: 'background.paper',
                      borderRadius: 1,
                    }}
                  >
                    <Typography variant="h6" gutterBottom>
                      No past appointments
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Your completed and cancelled appointments will appear here
                    </Typography>
                  </Box>
                </Grid>
              )}
            </Grid>

            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination page={page} onChange={(_: React.ChangeEvent<unknown>, p: number) => setPage(p)} count={10} color="primary" />
            </Box>
          </TabPanel>
        </>
      )}

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleSnackbarClose}
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default AppointmentListPage; 
