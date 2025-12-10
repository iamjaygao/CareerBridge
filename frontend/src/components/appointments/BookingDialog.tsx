import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import { DatePicker, TimePicker } from '@mui/x-date-pickers';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { format, addDays, isAfter, startOfDay } from 'date-fns';
import { Mentor } from '../../types';
import appointmentService from '../../services/api/appointmentService';

interface BookingDialogProps {
  open: boolean;
  onClose: () => void;
  mentor: Mentor | null;
  onBookingComplete?: () => void;
}

interface BookingFormData {
  date: Date | null;
  time: Date | null;
  duration: number;
  sessionType: string;
  notes: string;
}

const sessionTypes = [
  { value: 'resume_review', label: 'Resume Review' },
  { value: 'mock_interview', label: 'Mock Interview' },
  { value: 'career_advice', label: 'Career Advice' },
  { value: 'skill_coaching', label: 'Skill Coaching' },
  { value: 'job_search', label: 'Job Search Strategy' },
];

const durations = [
  { value: 30, label: '30 minutes' },
  { value: 60, label: '1 hour' },
  { value: 90, label: '1.5 hours' },
  { value: 120, label: '2 hours' },
];

const steps = ['Select Date & Time', 'Session Details', 'Confirm Booking'];

const BookingDialog: React.FC<BookingDialogProps> = ({
  open,
  onClose,
  mentor,
  onBookingComplete,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableSlots, setAvailableSlots] = useState<any[]>([]);
  const [formData, setFormData] = useState<BookingFormData>({
    date: null,
    time: null,
    duration: 60,
    sessionType: 'resume_review',
    notes: '',
  });

  useEffect(() => {
    if (open && mentor) {
      loadAvailableSlots();
    }
  }, [open, mentor]);

  const loadAvailableSlots = async (date?: Date) => {
    if (!mentor) return;
    
    try {
      setLoading(true);
      // Fetch available time slots for the selected date or today
      const targetDate = date || formData.date || new Date();
      const dateStr = format(targetDate, 'yyyy-MM-dd');
      const slots = await appointmentService.getAvailableTimeSlots(mentor.id, dateStr);
      setAvailableSlots(slots);
    } catch (error) {
      console.error('Failed to load available slots:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleSubmit = async () => {
    if (!mentor || !formData.date || !formData.time) return;

    try {
      setLoading(true);
      setError(null);

      const appointmentData = {
        mentor: mentor.id,
        date: format(formData.date, 'yyyy-MM-dd'),
        time: format(formData.time, 'HH:mm'),
        notes: formData.notes,
      };

      await appointmentService.createAppointment(appointmentData);
      
      onBookingComplete?.();
      onClose();
      setActiveStep(0);
      setFormData({
        date: null,
        time: null,
        duration: 60,
        sessionType: 'resume_review',
        notes: '',
      });
    } catch (error: any) {
      setError(error?.message || 'Failed to book appointment');
    } finally {
      setLoading(false);
    }
  };

  const getTotalPrice = () => {
    if (!mentor) return 0;
    const rate = mentor.hourly_rate || mentor.price_per_hour || 0;
    return rate * (formData.duration / 60);
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Select Date & Time
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <DatePicker
                  label="Date"
                  value={formData.date}
                  onChange={(newDate) => setFormData({ ...formData, date: newDate })}
                  minDate={startOfDay(new Date())}
                  maxDate={addDays(new Date(), 30)}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TimePicker
                  label="Time"
                  value={formData.time}
                  onChange={(newTime) => setFormData({ ...formData, time: newTime })}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Available Time Slots
                </Typography>
                {loading ? (
                  <CircularProgress size={20} />
                ) : (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {availableSlots.slice(0, 8).map((slot, index) => (
                      <Chip
                        key={index}
                        label={slot.time}
                        variant="outlined"
                        onClick={() => {
                          const [date, time] = slot.datetime.split('T');
                          setFormData({
                            ...formData,
                            date: new Date(date),
                            time: new Date(slot.datetime),
                          });
                        }}
                        color={formData.date === new Date(slot.date) && 
                               formData.time === new Date(slot.datetime) ? 'primary' : 'default'}
                      />
                    ))}
                  </Box>
                )}
              </Grid>
            </Grid>
          </LocalizationProvider>
        );

      case 1:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Session Details
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Session Type</InputLabel>
                <Select
                  value={formData.sessionType}
                  onChange={(e) => setFormData({ ...formData, sessionType: e.target.value })}
                  label="Session Type"
                >
                  {sessionTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Duration</InputLabel>
                <Select
                  value={formData.duration}
                  onChange={(e) => setFormData({ ...formData, duration: e.target.value as number })}
                  label="Duration"
                >
                  {durations.map((duration) => (
                    <MenuItem key={duration.value} value={duration.value}>
                      {duration.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Additional Notes"
                placeholder="Tell your mentor about your goals, questions, or specific topics you'd like to discuss..."
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        );

      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Confirm Booking
            </Typography>
            
            <Box sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1, mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Session Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Mentor
                  </Typography>
                  <Typography variant="body1">
                    {typeof mentor?.user === 'object' 
                      ? `${mentor.user.first_name || ''} ${mentor.user.last_name || ''}`.trim() || mentor.user.username
                      : 'Mentor'}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Date & Time
                  </Typography>
                  <Typography variant="body1">
                    {formData.date && formData.time && 
                     `${format(formData.date, 'MMM dd, yyyy')} at ${format(formData.time, 'HH:mm')}`}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Duration
                  </Typography>
                  <Typography variant="body1">
                    {formData.duration} minutes
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Session Type
                  </Typography>
                  <Typography variant="body1">
                    {sessionTypes.find(t => t.value === formData.sessionType)?.label}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">
                    Total Price
                  </Typography>
                  <Typography variant="h6" color="primary">
                    ${getTotalPrice().toFixed(2)}
                  </Typography>
                </Grid>
              </Grid>
            </Box>

            {formData.notes && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Notes
                </Typography>
                <Typography variant="body2">
                  {formData.notes}
                </Typography>
              </Box>
            )}
          </Box>
        );

      default:
        return null;
    }
  };

  if (!mentor) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="h5">
            Book Session with {typeof mentor?.user === 'object' 
              ? `${mentor.user.first_name || ''} ${mentor.user.last_name || ''}`.trim() || mentor.user.username
              : 'Mentor'}
          </Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {renderStepContent(activeStep)}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Box sx={{ flex: '1 1 auto' }} />
        {activeStep > 0 && (
          <Button onClick={handleBack} disabled={loading}>
            Back
          </Button>
        )}
        {activeStep < steps.length - 1 ? (
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={loading || !formData.date || !formData.time}
          >
            Next
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {loading ? 'Booking...' : 'Confirm Booking'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default BookingDialog; 