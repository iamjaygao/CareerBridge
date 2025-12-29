import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Button,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Visibility as ViewIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import appointmentService from '../../services/api/appointmentService';
import apiClient from '../../services/api/client';
import { Appointment } from '../../types';
import { format } from 'date-fns';

const StudentAppointmentsPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [appointments, setAppointments] = useState<Appointment[]>([]);

  useEffect(() => {
    fetchAppointments();
  }, []);

  useEffect(() => {
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
  }, [location.search, navigate]);

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
        const serviceTitle = apt.service?.title;
        
        return {
          id: apt.id,
          mentor: apt.mentor,
          user: apt.user,
          date: format(scheduledStart, 'yyyy-MM-dd'),
          time: format(scheduledStart, 'HH:mm'),
          status: apt.status,
          is_paid: apt.is_paid,
          notes: apt.description,
          meeting_link: apt.meeting_link,
          meeting_platform: apt.meeting_platform,
          user_feedback: apt.user_feedback,
          mentor_feedback: apt.mentor_feedback,
          user_rating: apt.user_rating,
          scheduled_start: apt.scheduled_start,
          scheduled_end: apt.scheduled_end,
          title: serviceTitle || apt.title,
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

  const getStatusChip = (status: string, isPaid?: boolean) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      pending: 'warning',
      confirmed: 'success',
      completed: 'info',
      cancelled: 'error',
      expired: 'error',
    };
    const labels: Record<string, string> = {
      pending: isPaid ? 'Pending Confirmation' : 'Pending Payment',
      confirmed: 'Confirmed',
      completed: 'Completed',
      cancelled: 'Cancelled',
      expired: 'Expired',
    };
    return (
      <Chip
        label={labels[status] || status.charAt(0).toUpperCase() + status.slice(1)}
        color={colors[status] || 'default'}
        size="small"
      />
    );
  };

  const formatDateTime = (dateString: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return format(date, 'MMM dd, yyyy HH:mm');
  };

  const getMentorName = (mentor: any): string => {
    if (typeof mentor === 'object' && mentor !== null) {
      if (mentor.user) {
        const firstName = mentor.user.first_name || '';
        const lastName = mentor.user.last_name || '';
        const fullName = `${firstName} ${lastName}`.trim();
        return fullName || mentor.user.username || 'Mentor';
      }
      return mentor.name || 'Mentor';
    }
    return 'Mentor';
  };

  const getDuration = (appointment: Appointment): number => {
    if (appointment.scheduled_start && appointment.scheduled_end) {
      const start = new Date(appointment.scheduled_start);
      const end = new Date(appointment.scheduled_end);
      return Math.round((end.getTime() - start.getTime()) / (1000 * 60));
    }
    return 60; // default
  };

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

  if (loading) {
    return <LoadingSpinner message="Loading appointments..." />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  const displayedAppointments = tabValue === 0 ? upcomingAppointments : pastAppointments;

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          My Appointments
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Manage your mentor sessions
        </Typography>
      </Box>

      {/* Tabs */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
            <Tab label={`Upcoming (${upcomingAppointments.length})`} />
            <Tab label={`Past (${pastAppointments.length})`} />
          </Tabs>
        </CardContent>
      </Card>

      {/* Appointments Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Mentor</TableCell>
                  <TableCell>Date & Time</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Topic</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {displayedAppointments.length > 0 ? (
                  displayedAppointments.map((appointment) => {
                    const mentor = typeof appointment.mentor === 'object' ? appointment.mentor : null;
                    const mentorName = getMentorName(appointment.mentor);
                    const mentorInitial = mentorName.charAt(0).toUpperCase();
                    
                    return (
                      <TableRow key={appointment.id} hover>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Box
                              sx={{
                                width: 32,
                                height: 32,
                                borderRadius: '50%',
                                bgcolor: 'primary.main',
                                color: 'white',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                mr: 2,
                                fontSize: '0.875rem',
                                fontWeight: 600,
                              }}
                            >
                              {mentorInitial}
                            </Box>
                            <Typography variant="body2" fontWeight="medium">
                              {mentorName}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {appointment.scheduled_start ? formatDateTime(appointment.scheduled_start) : 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {getDuration(appointment)} min
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                            {appointment.title || appointment.notes || 'Career Guidance'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {getStatusChip(appointment.status, appointment.is_paid)}
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={() => navigate(`/student/appointments/${appointment.id}`)}
                            color="primary"
                          >
                            <ViewIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    );
                  })
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                      <Typography variant="body2" color="text.secondary">
                        {tabValue === 0
                          ? 'No upcoming appointments'
                          : 'No past appointments'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default StudentAppointmentsPage;
