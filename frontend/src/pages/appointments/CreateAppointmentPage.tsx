import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Paper,
  Avatar,
  Chip,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import { format, addDays } from 'date-fns';

import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import { useNotification } from '../../components/common/NotificationProvider';
import mentorService from '../../services/api/mentorService';
import appointmentService from '../../services/api/appointmentService';
import apiClient from '../../services/api/client';
import { MentorDetail } from '../../types';
import type { ApiError } from '../../services/utils/errorHandler';
import { handleApiError } from '../../services/utils/errorHandler';

interface CreateAppointmentForm {
  mentor_id: number;
  service_id: number;
  scheduled_date: Date | null;
  user_notes: string;
}

interface TimeSlot {
  id: number;
  start_time: string;
  end_time: string;
}

const steps = ['Select Mentor & Service', 'Choose Date & Time', 'Review & Confirm'];

const CreateAppointmentPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { showSuccess, showError } = useNotification();
  
  const [activeStep, setActiveStep] = useState(0);
  const [pageLoading, setPageLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [mentors, setMentors] = useState<any[]>([]);
  const [selectedMentor, setSelectedMentor] = useState<MentorDetail | null>(null);
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [selectedSlotId, setSelectedSlotId] = useState<number | null>(null);
  const selectedSlot = availableSlots.find(s => s.id === selectedSlotId);

  
  
  const [form, setForm] = useState<CreateAppointmentForm>({
    mentor_id: 0,
    service_id: 0,
    scheduled_date: null,
    user_notes: '',
  });

  // Check if mentor_id is passed from location state or URL params
  useEffect(() => {
    const state = location.state as { mentor_id?: number };
    const urlParams = new URLSearchParams(location.search);
    const mentorIdFromUrl = urlParams.get('mentor');
    
    if (state?.mentor_id) {
      setForm(prev => ({ ...prev, mentor_id: state.mentor_id! }));
    } else if (mentorIdFromUrl) {
      setForm(prev => ({ ...prev, mentor_id: parseInt(mentorIdFromUrl) }));
    }
    fetchMentors();
  }, [location.state, location.search]);

  const fetchMentors = async () => {
    try {
      setPageLoading(true);
      const mentorsData = await mentorService.getMentors();
      setMentors(mentorsData);
    } catch (err) {
      setError(handleApiError(err));
      console.error('Mentors fetch error:', err);
    } finally {
      setPageLoading(false);
    }
  };

  const fetchAvailableSlots = async (mentorId: number, date: Date, serviceId?: number) => {
    try {
      setLoadingSlots(true);
      const formattedDate = format(date, 'yyyy-MM-dd');
      const params: any = {
        mentor_id: mentorId,
        date: formattedDate,
      };
      if (serviceId) {
        params.service_id = serviceId;
      }
      const { OS_API } = await import('../../os/apiPaths');
      const response = await apiClient.get(`${OS_API.DECISION_SLOTS}time-slots/`, { params });
      const slots = response.data || [];
      setAvailableSlots(slots);
    } catch (err) {
      console.error('Failed to fetch available slots:', err);
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleMentorChange = (mentorId: number) => {
    const mentor = mentors.find(m => m.id === mentorId);
    setSelectedMentor(mentor || null);
    setForm(prev => ({ 
      ...prev, 
      mentor_id: mentorId, 
      service_id: 0,
      scheduled_date: null,
    }));
    setAvailableSlots([]);
    setSelectedSlotId(null);
    setActiveStep(0);
  };

  const handleServiceChange = (serviceId: number) => {
    setForm(prev => {
      const newForm = { ...prev, service_id: serviceId };
      setSelectedSlotId(null);
      if (newForm.scheduled_date && newForm.mentor_id) {
        fetchAvailableSlots(newForm.mentor_id, newForm.scheduled_date, serviceId);
      }
      return newForm;
    });
  };

  const handleDateChange = (date: Date | null) => {
    setForm(prev => ({ ...prev, scheduled_date: date }));
    setSelectedSlotId(null);
    setAvailableSlots([]);
    if (date && form.mentor_id) {
      fetchAvailableSlots(form.mentor_id, date, form.service_id || undefined);
    }
  };

  const handleNext = () => {
    if (activeStep === 0 && (!form.mentor_id || !form.service_id)) {
      showError('Please select a mentor and service');
      return;
    }
    if (activeStep === 1 && (!form.scheduled_date || !selectedSlotId)) {
      showError('Please select a date and time');
      return;
    }
    setActiveStep(prev => prev + 1);
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const handleSubmit = async () => {
    if (!selectedSlotId) {
      showError('Please select a time slot');
      return;
    }
    
    if (!form.service_id) {
      showError('Service is required to book a time slot');
      return;
    }
  
    try {
      setSubmitLoading(true);
  
      const res = await appointmentService.lockSlot({
        time_slot_id: selectedSlotId,
        service_id: form.service_id,
        title: selectedService?.title,
        description: form.user_notes,
      });
  
      showSuccess('Time slot reserved. Please complete payment.');
  
      // Next: go to appointment detail page
      navigate(`/student/appointments/${res.appointment.id}`);
    } catch (err: any) {
      let errorMessage = 'Failed to reserve time slot. Please try again.';
      if (err?.response?.status === 409) {
        errorMessage = 'This time slot was just booked by someone else. Please choose another one.';
      } else if (err?.response?.status === 400) {
        errorMessage = 'This time slot is no longer available.';
      }
      showError(errorMessage);
      console.error(err);
    } finally {
      setSubmitLoading(false);
    }
  };

  if (pageLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorAlert error={error} />;
  }

  const selectedService = selectedMentor?.services?.find(s => s.id === form.service_id);

  return (
    <>
      <PageHeader
        title="Create Appointment"
        breadcrumbs={[
          { label: 'Appointments', path: '/student/appointments' },
          { label: 'Create', path: '/student/appointments/create' }
        ]}
        action={
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/student/appointments')}
          >
            Back to Appointments
          </Button>
        }
      />

      <Container maxWidth="md">
        <Card>
          <CardContent>
            <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
              {steps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>

            {/* Step 1: Select Mentor & Service */}
            {activeStep === 0 && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Select Mentor & Service
                </Typography>
                
                <FormControl fullWidth sx={{ mb: 3 }}>
                  <InputLabel>Select Mentor</InputLabel>
                  <Select
                    value={form.mentor_id}
                    onChange={(e) => handleMentorChange(e.target.value as number)}
                    label="Select Mentor"
                  >
                    {mentors.map((mentor) => (
                      <MenuItem key={mentor.id} value={mentor.id}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar sx={{ width: 32, height: 32, mr: 2 }}>
                            {mentor.user.first_name[0]}{mentor.user.last_name[0]}
                          </Avatar>
                          <Box>
                            <Typography variant="body1">
                              {mentor.user.first_name} {mentor.user.last_name}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {mentor.current_position} • {mentor.industry}
                            </Typography>
                          </Box>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {selectedMentor && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Services Offered by {selectedMentor.user.first_name}
                    </Typography>
                    <Grid container spacing={2}>
                      {selectedMentor.services?.map((service) => (
                        <Grid item xs={12} key={service.id}>
                          <Paper 
                            sx={{ 
                              p: 2, 
                              cursor: 'pointer',
                              border: form.service_id === service.id ? 2 : 1,
                              borderColor: form.service_id === service.id ? 'primary.main' : 'divider',
                              '&:hover': { borderColor: 'primary.main' }
                            }}
                            onClick={() => handleServiceChange(service.id)}
                          >
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                              <Box>
                                <Typography variant="h6">{service.title}</Typography>
                                <Typography variant="body2" color="text.secondary" paragraph>
                                  {service.description}
                                </Typography>
                                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                                  <Chip 
                                    label={service.service_type.replace('_', ' ')} 
                                    size="small" 
                                    color="primary" 
                                  />
                                  <Typography variant="body2">
                                    Duration: {service.duration_minutes} minutes
                                  </Typography>
                                </Box>
                              </Box>
                              <Box sx={{ textAlign: 'right' }}>
                                <Typography variant="h6" color="primary">
                                  {service.display_price}
                                </Typography>
                                {form.service_id === service.id && (
                                  <CheckIcon color="primary" />
                                )}
                              </Box>
                            </Box>
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                )}
              </Box>
            )}

            {/* Step 2: Choose Date & Time */}
            {activeStep === 1 && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Choose Date & Time
                </Typography>
                
                <TextField
                  type="date"
                  label="Select Date"
                  value={form.scheduled_date ? format(form.scheduled_date, 'yyyy-MM-dd') : ''}
                  onChange={(e) => {
                    const date = e.target.value ? new Date(e.target.value) : null;
                    handleDateChange(date);
                  }}
                  inputProps={{
                    min: format(addDays(new Date(), 1), 'yyyy-MM-dd')
                  }}
                  fullWidth
                  sx={{ mb: 3 }}
                />

                {form.scheduled_date && (
                  <FormControl fullWidth sx={{ mb: 3 }}>
                    <InputLabel>Select Time</InputLabel>
                    <Select
                      value={selectedSlotId ?? ''}
                      onChange={(e) => setSelectedSlotId(e.target.value as number)}
                      label="Select Time"
                      disabled={loadingSlots}
                    >
                      {loadingSlots && (
                        <MenuItem disabled>
                          <CircularProgress size={20} sx={{ mr: 1 }} />
                          Loading available slots...
                        </MenuItem>
                      )}

                      {!loadingSlots && availableSlots.length === 0 && (
                        <MenuItem disabled>No available slots</MenuItem>
                      )}

                      {availableSlots.map((slot) => {
                        const startTime = slot.start_time ? format(new Date(slot.start_time), 'HH:mm') : '';
                        const endTime = slot.end_time ? format(new Date(slot.end_time), 'HH:mm') : '';
                        return (
                          <MenuItem key={slot.id} value={slot.id}>
                            {startTime} – {endTime}
                          </MenuItem>
                        );
                      })}
                    </Select>
                  </FormControl>
                )}

                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Notes (Optional)"
                  value={form.user_notes}
                  onChange={(e) => setForm(prev => ({ ...prev, user_notes: e.target.value }))}
                  placeholder="Any specific topics or questions you'd like to discuss..."
                />
              </Box>
            )}

            {/* Step 3: Review & Confirm */}
            {activeStep === 2 && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Review & Confirm
                </Typography>
                
                <Paper sx={{ p: 3, mb: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Appointment Details
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Mentor
                      </Typography>
                      <Typography variant="body1">
                        {selectedMentor
                          ? `${selectedMentor.user.first_name} ${selectedMentor.user.last_name}`
                          : ''}
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Service
                      </Typography>
                      <Typography variant="body1">
                        {selectedService?.title}
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Date
                      </Typography>
                      <Typography variant="body1">
                        {form.scheduled_date ? format(form.scheduled_date, 'EEEE, MMMM dd, yyyy') : ''}
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Time
                      </Typography>

                      <Typography variant="body1">
                        {selectedSlot
                          ? `${selectedSlot.start_time} – ${selectedSlot.end_time}`
                          : ''}
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Duration
                      </Typography>
                      <Typography variant="body1">
                        {selectedService?.duration_minutes} minutes
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Price
                      </Typography>
                      <Typography variant="body1" color="primary" fontWeight="bold">
                        {selectedService?.display_price}
                      </Typography>
                    </Grid>
                    
                    {form.user_notes && (
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          Notes
                        </Typography>
                        <Typography variant="body1">
                          {form.user_notes}
                        </Typography>
                      </Grid>
                    )}
                  </Grid>
                </Paper>

                <Alert severity="info" sx={{ mb: 3 }}>
                  Please review your appointment details above. Once confirmed, you'll receive a confirmation email and the mentor will be notified of your booking.
                </Alert>
              </Box>
            )}

            {/* Navigation Buttons */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
              <Button
                disabled={activeStep === 0}
                onClick={handleBack}
              >
                Back
              </Button>
              
              <Box>
                {activeStep === steps.length - 1 ? (
                  <Button
                    variant="contained"
                    onClick={handleSubmit}
                    disabled={submitLoading}
                    startIcon={submitLoading ? <CircularProgress size={20} /> : undefined}
                  >
                    {submitLoading ? 'Reserving...' : 'Confirm & Pay'}
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    onClick={handleNext}
                  >
                    Next
                  </Button>
                )}
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </>
  );
};

export default CreateAppointmentPage; 
