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
import { MentorDetail } from '../../types';

interface CreateAppointmentForm {
  mentor_id: number;
  service_id: number;
  scheduled_date: Date | null;
  scheduled_time: string;
  user_notes: string;
}

const steps = ['Select Mentor & Service', 'Choose Date & Time', 'Review & Confirm'];

const CreateAppointmentPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { showSuccess, showError } = useNotification();
  
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mentors, setMentors] = useState<any[]>([]);
  const [selectedMentor, setSelectedMentor] = useState<MentorDetail | null>(null);
  const [availableSlots, setAvailableSlots] = useState<string[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  
  const [form, setForm] = useState<CreateAppointmentForm>({
    mentor_id: 0,
    service_id: 0,
    scheduled_date: null,
    scheduled_time: '',
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
      setLoading(true);
      const mentorsData = await mentorService.getMentors();
      setMentors(mentorsData);
    } catch (err) {
      setError('Failed to load mentors');
      console.error('Mentors fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableSlots = async (mentorId: number, date: Date) => {
    try {
      setLoadingSlots(true);
      const formattedDate = format(date, 'yyyy-MM-dd');
      const slots = await mentorService.getMentorAvailability(mentorId, formattedDate);
      setAvailableSlots(slots.map((slot: any) => slot.start_time));
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
      scheduled_time: ''
    }));
    setActiveStep(0);
  };

  const handleServiceChange = (serviceId: number) => {
    setForm(prev => ({ ...prev, service_id: serviceId }));
  };

  const handleDateChange = (date: Date | null) => {
    setForm(prev => ({ ...prev, scheduled_date: date, scheduled_time: '' }));
    if (date && form.mentor_id) {
      fetchAvailableSlots(form.mentor_id, date);
    }
  };

  const handleNext = () => {
    if (activeStep === 0 && (!form.mentor_id || !form.service_id)) {
      showError('Please select a mentor and service');
      return;
    }
    if (activeStep === 1 && (!form.scheduled_date || !form.scheduled_time)) {
      showError('Please select a date and time');
      return;
    }
    setActiveStep(prev => prev + 1);
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const handleSubmit = async () => {
    if (!form.scheduled_date) return;

    try {
      setLoading(true);
      const appointmentData = {
        mentor: form.mentor_id,
        date: format(form.scheduled_date, 'yyyy-MM-dd'),
        time: form.scheduled_time,
        notes: form.user_notes,
      };

      await appointmentService.createAppointment(appointmentData);
      showSuccess('Appointment created successfully!');
      navigate('/appointments');
    } catch (err) {
      showError('Failed to create appointment');
      console.error('Appointment creation error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  const selectedService = selectedMentor?.services?.find(s => s.id === form.service_id);

  return (
    <>
      <PageHeader
        title="Create Appointment"
        breadcrumbs={[
          { label: 'Appointments', path: '/appointments' },
          { label: 'Create', path: '/appointments/create' }
        ]}
        action={
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/appointments')}
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
                      value={form.scheduled_time}
                      onChange={(e) => setForm(prev => ({ ...prev, scheduled_time: e.target.value }))}
                      label="Select Time"
                      disabled={loadingSlots}
                    >
                      {loadingSlots ? (
                        <MenuItem disabled>
                          <CircularProgress size={20} sx={{ mr: 1 }} />
                          Loading available slots...
                        </MenuItem>
                      ) : availableSlots.length === 0 ? (
                        <MenuItem disabled>No available slots for this date</MenuItem>
                      ) : (
                        availableSlots.map((slot) => (
                          <MenuItem key={slot} value={slot}>
                            {slot}
                          </MenuItem>
                        ))
                      )}
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
                        {selectedMentor?.user.first_name} {selectedMentor?.user.last_name}
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
                        {form.scheduled_time}
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
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={20} /> : undefined}
                  >
                    {loading ? 'Creating...' : 'Create Appointment'}
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