import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Alert,
  CircularProgress,
  Paper,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';

import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import { useNotification } from '../../components/common/NotificationProvider';
import appointmentService from '../../services/api/appointmentService';
import apiClient from '../../services/api/client';

const parseWallTime = (iso: string): Date => {
  return new Date(iso);
};

interface TimeSlot {
  id: number;
  start_time: string;
  end_time: string;
  mentor_id?: number;
  price?: string;
  currency?: string;
}

interface UISlot {
  parent_slot_id: number;
  start_time: string;
  end_time: string;
}

const splitSlotsIntoHours = (slots: TimeSlot[]): UISlot[] => {
  const result: UISlot[] = [];
  const now = new Date();

  slots.forEach((slot) => {
    let cursor = parseWallTime(slot.start_time);
    const end = parseWallTime(slot.end_time);

    if (cursor.getTime() <= now.getTime()) {
      return;
    }

    while (cursor.getTime() + 60 * 60 * 1000 <= end.getTime()) {
      const next = new Date(cursor.getTime() + 60 * 60 * 1000);

      if (cursor.getTime() > now.getTime()) {
        result.push({
          parent_slot_id: slot.id,
          start_time: cursor.toISOString(),
          end_time: next.toISOString(),
        });
      }

      cursor = next;
    }
  });

  return result;
};

const RescheduleAppointmentPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();
  
  const [loading, setLoading] = useState(true);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [appointment, setAppointment] = useState<any>(null);
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [uiSlots, setUiSlots] = useState<UISlot[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [slotsLoaded, setSlotsLoaded] = useState(false);
  const [weekOffset, setWeekOffset] = useState(0);
  const [selectedSlotId, setSelectedSlotId] = useState<number | null>(null);
  const [selectedUiSlot, setSelectedUiSlot] = useState<UISlot | null>(null);
  const [selectedServiceId, setSelectedServiceId] = useState<number | null>(null);

  useEffect(() => {
    if (id) {
      fetchAppointment();
    }
  }, [id]);

  const getServiceIdFromAppointment = (data: any): number | null => {
    if (data?.service_id) {
      return data.service_id;
    }

    if (data?.mentor?.services && data?.title) {
      const matchingService = data.mentor.services.find(
        (s: any) => s.title === data.title || s.id === data.mentor.primary_service_id
      );
      return matchingService?.id || data.mentor.primary_service_id || null;
    }

    if (data?.mentor?.primary_service_id) {
      return data.mentor.primary_service_id;
    }

    return null;
  };

  const fetchAppointment = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      setError(null);
      const data = await appointmentService.getAppointmentById(parseInt(id));
      setAppointment(data);
      
      if (data.status !== 'confirmed') {
        setError('Only confirmed appointments can be rescheduled');
        return;
      }

      const serviceId = getServiceIdFromAppointment(data);
      setSelectedServiceId(serviceId);

      if (data.mentor?.id) {
        fetchAvailableSlots(data.mentor.id, weekOffset, serviceId);
      }
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to load appointment');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableSlots = useCallback(async (mentorId: number, offset: number, serviceId?: number | null) => {
    try {
      setLoadingSlots(true);
      setSlotsLoaded(false);

      const today = new Date();
      const baseDate = new Date(today);
      baseDate.setDate(today.getDate() + offset * 7);

      const dayOfWeek = baseDate.getDay();
      const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
      const monday = new Date(baseDate);
      monday.setDate(baseDate.getDate() + mondayOffset);
      monday.setHours(0, 0, 0, 0);

      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);
      sunday.setHours(23, 59, 59, 999);

      const params: any = {
        mentor_id: mentorId,
        from: format(monday, 'yyyy-MM-dd'),
        to: format(sunday, 'yyyy-MM-dd'),
      };

      if (serviceId) params.service_id = serviceId;

      const response = await apiClient.get('/appointments/time-slots/', { params });
      const slots = response.data || [];
      setAvailableSlots(slots);
      setUiSlots(splitSlotsIntoHours(slots));
      setSlotsLoaded(true);
    } catch (err) {
      console.error('Failed to fetch available slots:', err);
      setAvailableSlots([]);
      setUiSlots([]);
      setSlotsLoaded(true);
    } finally {
      setLoadingSlots(false);
    }
  }, []);

  useEffect(() => {
    if (!appointment?.mentor?.id) return;
    fetchAvailableSlots(appointment.mentor.id, weekOffset, selectedServiceId);
  }, [appointment?.mentor?.id, weekOffset, selectedServiceId, fetchAvailableSlots]);

  const handleWeekChange = (offset: number) => {
    setWeekOffset(offset);
    setSelectedSlotId(null);
    setSelectedUiSlot(null);
  };

  const handleSlotSelect = (slot: UISlot) => {
    setSelectedSlotId(slot.parent_slot_id);
    setSelectedUiSlot(slot);
  };

  const handleSubmit = async () => {
    if (!selectedSlotId) {
      showError('Please select a time slot');
      return;
    }
    
    if (!appointment?.id) {
      showError('Appointment information is missing');
      return;
    }
    
    if (!appointment?.mentor?.id) {
      showError('Mentor information is missing');
      return;
    }

    const serviceId = getServiceIdFromAppointment(appointment);
    
    if (!serviceId) {
      showError('Could not determine service. Please contact support.');
      return;
    }
  
    try {
      setSubmitLoading(true);
  
      const res = await appointmentService.lockSlot({
        appointment_id: appointment.id,
        time_slot_id: selectedSlotId,
        service_id: serviceId,
      });
  
      showSuccess('Appointment rescheduled successfully');
      navigate(`/student/appointments/${res.appointment.id}`);
    } catch (err: any) {
      let errorMessage = 'Failed to reschedule appointment. Please try again.';
      if (err?.response?.status === 409) {
        errorMessage = 'This time slot was just booked by someone else. Please choose another one.';
      } else if (err?.response?.status === 400) {
        errorMessage = err?.response?.data?.error || 'This time slot is no longer available.';
      }
      showError(errorMessage);
      console.error(err);
    } finally {
      setSubmitLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  if (!appointment) {
    return <ErrorAlert message="Appointment not found" />;
  }

  if (appointment.status !== 'confirmed') {
    return <ErrorAlert message="Only confirmed appointments can be rescheduled" />;
  }

  const mentorName = appointment.mentor?.user
    ? `${appointment.mentor.user.first_name || ''} ${appointment.mentor.user.last_name || ''}`.trim() || appointment.mentor.user.username
    : 'Mentor';

  const originalStart = new Date(appointment.scheduled_start);
  const originalEnd = new Date(appointment.scheduled_end);

  return (
    <>
      <PageHeader
        title="Reschedule Appointment"
        breadcrumbs={[
          { label: 'Appointments', path: '/student/appointments' },
          { label: 'Details', path: `/student/appointments/${id}` },
          { label: 'Reschedule', path: `/student/appointments/${id}/reschedule` }
        ]}
        action={
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate(`/student/appointments/${id}`)}
          >
            Back to Details
          </Button>
        }
      />

      <Container maxWidth="md">
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Reschedule Appointment
            </Typography>
            
            <Alert severity="info" sx={{ mb: 3 }}>
              Select a new date and time for your appointment. The original appointment will be replaced.
            </Alert>

            <Paper sx={{ p: 3, mb: 3, bgcolor: 'grey.50' }}>
              <Typography variant="subtitle1" gutterBottom>
                Current Appointment Details
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Mentor
                  </Typography>
                  <Typography variant="body1">
                    {mentorName}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Service
                  </Typography>
                  <Typography variant="body1">
                    {appointment.title || 'Career Guidance'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Original Date & Time
                  </Typography>
                  <Typography variant="body1">
                    {format(originalStart, 'EEEE, MMMM dd, yyyy')} at {format(originalStart, 'HH:mm')} – {format(originalEnd, 'HH:mm')}
                  </Typography>
                </Grid>
              </Grid>
            </Paper>

            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Button
                  variant={weekOffset === 0 ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => handleWeekChange(0)}
                  disabled={weekOffset === 0}
                >
                  This Week
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => handleWeekChange(weekOffset + 1)}
                >
                  Next Week
                </Button>
              </Box>

              {loadingSlots || !slotsLoaded ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography>Loading available slots...</Typography>
                </Box>
              ) : slotsLoaded && uiSlots.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography color="text.secondary">No available slots this week</Typography>
                </Box>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, maxHeight: 400, overflow: 'auto' }}>
                  {uiSlots.map((slot) => {
                    const start = parseWallTime(slot.start_time);
                    const end = parseWallTime(slot.end_time);
                    const dateStr = format(start, 'MMM dd');
                    const startTimeStr = format(start, 'HH:mm');
                    const endTimeStr = format(end, 'HH:mm');
                    const isSelected = selectedUiSlot?.start_time === slot.start_time && selectedUiSlot?.parent_slot_id === slot.parent_slot_id;

                    return (
                      <Button
                        key={`${slot.parent_slot_id}-${slot.start_time}`}
                        variant={isSelected ? 'contained' : 'outlined'}
                        fullWidth
                        onClick={() => handleSlotSelect(slot)}
                        sx={{
                          justifyContent: 'flex-start',
                          textTransform: 'none',
                          py: 1.5,
                        }}
                      >
                        <Typography>
                          {dateStr} • {startTimeStr} – {endTimeStr}
                        </Typography>
                      </Button>
                    );
                  })}
                </Box>
              )}
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
              <Button
                onClick={() => navigate(`/student/appointments/${id}`)}
                disabled={submitLoading}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                onClick={handleSubmit}
                disabled={submitLoading || !selectedSlotId}
                startIcon={submitLoading ? <CircularProgress size={20} /> : undefined}
              >
                {submitLoading ? 'Rescheduling...' : 'Confirm Reschedule'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </>
  );
};

export default RescheduleAppointmentPage;
