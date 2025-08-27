import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
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
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { AppDispatch, RootState } from '../../store';
import { fetchAppointments, setFilters } from '../../store/slices/appointmentSlice';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import AppointmentCard from '../../components/appointments/AppointmentCard';
import { AppointmentFilters } from '../../services/api/appointmentService';

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
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { appointments, loading, error, filters } = useSelector((state: RootState) => state.appointments);
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

  useEffect(() => {
    const defaultFilters: AppointmentFilters = {
      status: tabValue === 0 ? 'upcoming' : 'past',
      page,
    };
    dispatch(setFilters(defaultFilters));
    dispatch(fetchAppointments(defaultFilters));
  }, [dispatch, tabValue, page]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleReschedule = (appointmentId: number) => {
    navigate(`/appointments/${appointmentId}/reschedule`);
  };

  const handleNewAppointment = () => {
    navigate('/appointments/create');
  };

  const handleSnackbarClose = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const upcomingAppointments = appointments.filter(
    (apt) => apt.status === 'confirmed' || apt.status === 'pending'
  );
  const pastAppointments = appointments.filter(
    (apt) => apt.status === 'completed' || apt.status === 'cancelled'
  );

  if (loading) {
    return <LoadingSpinner message="Loading appointments..." />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  return (
    <>
      <PageHeader
        title="My Appointments"
        breadcrumbs={[{ label: 'Appointments', path: '/appointments' }]}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleNewAppointment}
          >
            Book Appointment
          </Button>
        }
      />

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
              dispatch(setFilters({ ...filters, sort_by: e.target.value }))
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
                dispatch(setFilters({ ...filters, status: e.target.value }))
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
          <Pagination page={page} onChange={(_, p) => setPage(p)} count={10} color="primary" />
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
          <Pagination page={page} onChange={(_, p) => setPage(p)} count={10} color="primary" />
        </Box>
      </TabPanel>

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