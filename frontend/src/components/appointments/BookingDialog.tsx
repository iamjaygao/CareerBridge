import React, { useEffect, useMemo, useState } from 'react';
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
import { format, addDays, startOfDay } from 'date-fns';

import apiClient from '../../services/api/client';
import appointmentService from '../../services/api/appointmentService';
import { Mentor } from '../../types';

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

type NormalizedSlot = {
  key: string;
  label: string;
  date: string; // yyyy-MM-dd
  time: string; // HH:mm
};

function normalizeSlots(raw: any, fallbackDateStr: string): NormalizedSlot[] {
  const arr: any[] = Array.isArray(raw)
    ? raw
    : Array.isArray(raw?.results)
      ? raw.results
      : [];

  const slots: NormalizedSlot[] = [];

  for (let i = 0; i < arr.length; i += 1) {
    const s = arr[i] ?? {};

    let dateStr: string | null = null;
    let timeStr: string | null = null;

    // 1) { datetime: "2025-12-22T03:00:00Z" }
    if (typeof s.datetime === 'string') {
      const parts = s.datetime.split('T');
      if (parts.length >= 2) {
        dateStr = parts[0] || null;
        const hhmm = parts[1]?.slice(0, 5);
        timeStr = hhmm || null;
      }
    }

    // 2) { date: "yyyy-MM-dd" }
    if (!dateStr && typeof s.date === 'string') dateStr = s.date;

    // 3) { time: "HH:mm" }
    if (!timeStr && typeof s.time === 'string') timeStr = s.time.slice(0, 5);

    // 4) { start_time: "HH:mm:ss" | "HH:mm" }
    if (!timeStr && typeof s.start_time === 'string') {
      timeStr = s.start_time.slice(0, 5);
    }

    if (!dateStr) dateStr = fallbackDateStr;
    if (!dateStr || !timeStr) continue;

    slots.push({
      key: `${dateStr}-${timeStr}-${i}`,
      label: timeStr,
      date: dateStr,
      time: timeStr,
    });
  }

  return slots;
}

const BookingDialog: React.FC<BookingDialogProps> = ({
  open,
  onClose,
  mentor,
  onBookingComplete,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Raw slots from backend (unknown schema)
  const [rawSlots, setRawSlots] = useState<any>([]);

  const [formData, setFormData] = useState<BookingFormData>({
    date: null,
    time: null,
    duration: 60,
    sessionType: 'resume_review',
    notes: '',
  });

  const selectedDateStr = useMemo(() => {
    const d = formData.date ?? new Date();
    return format(d, 'yyyy-MM-dd');
  }, [formData.date]);

  const normalizedSlots: NormalizedSlot[] = useMemo(() => {
    return normalizeSlots(rawSlots, selectedDateStr);
  }, [rawSlots, selectedDateStr]);

  // Load slots when dialog opens or mentor/date changes
  useEffect(() => {
    if (!open || !mentor) return;

    // If date not set yet, set to today and let effect re-run
    if (!formData.date) {
      setFormData((prev) => ({ ...prev, date: startOfDay(new Date()), time: null }));
      return;
    }

    const load = async () => {
      try {
        setLoadingSlots(true);
        setError(null);

        const dateStr = format(formData.date!, 'yyyy-MM-dd');

        // ✅ backend urls.py has: path('time-slots/', ...)
        const resp = await apiClient.get('/appointments/time-slots/', {
          params: { mentor: mentor.id, date: dateStr },
        });

        setRawSlots(resp.data);
      } catch (e: any) {
        console.error('Failed to load time slots:', e);
        setRawSlots([]);
        setError('Failed to load available time slots.');
      } finally {
        setLoadingSlots(false);
      }
    };

    load();
  }, [open, mentor?.id, formData.date, mentor]);

  const handleNext = () => setActiveStep((p) => p + 1);
  const handleBack = () => setActiveStep((p) => p - 1);

  const resetState = () => {
    setActiveStep(0);
    setError(null);
    setRawSlots([]);
    setSubmitting(false);
    setLoadingSlots(false);
    setFormData({
      date: null,
      time: null,
      duration: 60,
      sessionType: 'resume_review',
      notes: '',
    });
  };

  const handleClose = () => {
    onClose();
    resetState();
  };

  const handleSubmit = async () => {
    if (!mentor || !formData.date || !formData.time) return;

    try {
      setSubmitting(true);
      setError(null);

      // ✅ match appointmentService.createAppointment signature:
      // { mentor, date, time, notes? }
      await appointmentService.createAppointment({
        mentor: mentor.id,
        date: format(formData.date, 'yyyy-MM-dd'),
        time: format(formData.time, 'HH:mm'),
        notes: formData.notes,
      });

      onBookingComplete?.();
      handleClose();
    } catch (e: any) {
      console.error('Failed to book appointment:', e);
      setError(e?.message || 'Failed to book appointment');
    } finally {
      setSubmitting(false);
    }
  };

  const getTotalPrice = () => {
    if (!mentor) return null;

    const rate =
      mentor.starting_price && mentor.starting_price > 0
        ? mentor.starting_price
        : mentor.hourly_rate && mentor.hourly_rate > 0
          ? mentor.hourly_rate
          : null;

    if (rate === null) return null;
    return rate * (formData.duration / 60);
  };

  const totalPrice = getTotalPrice();

  const isNextDisabled =
    submitting ||
    loadingSlots ||
    !formData.date ||
    !formData.time;

  if (!mentor) return null;

  const displayMentorName =
    typeof mentor.user === 'object'
      ? `${mentor.user.first_name || ''} ${mentor.user.last_name || ''}`.trim() || mentor.user.username
      : 'Mentor';

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
                  onChange={(newDate) => {
                    setFormData((prev) => ({
                      ...prev,
                      date: newDate,
                      time: null,
                    }));
                  }}
                  minDate={startOfDay(new Date())}
                  maxDate={addDays(new Date(), 14)}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TimePicker
                  label="Time"
                  value={formData.time}
                  onChange={(newTime) => setFormData((prev) => ({ ...prev, time: newTime }))}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Available Time Slots
                </Typography>

                {loadingSlots ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={18} />
                    <Typography variant="body2" color="text.secondary">
                      Loading slots...
                    </Typography>
                  </Box>
                ) : normalizedSlots.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    No available slots for selected date.
                  </Typography>
                ) : (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {normalizedSlots.slice(0, 12).map((slot) => {
                      const isSelected =
                        !!formData.date &&
                        format(formData.date, 'yyyy-MM-dd') === slot.date &&
                        !!formData.time &&
                        format(formData.time, 'HH:mm') === slot.time;

                      return (
                        <Chip
                          key={slot.key}
                          label={slot.label}
                          variant={isSelected ? 'filled' : 'outlined'}
                          color={isSelected ? 'primary' : 'default'}
                          onClick={() => {
                            const d = new Date(`${slot.date}T00:00:00`);
                            const t = new Date(`${slot.date}T${slot.time}:00`);
                            setFormData((prev) => ({
                              ...prev,
                              date: d,
                              time: t,
                            }));
                          }}
                        />
                      );
                    })}
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
                  onChange={(e) => setFormData((prev) => ({ ...prev, sessionType: e.target.value }))}
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
                  onChange={(e) => setFormData((prev) => ({ ...prev, duration: e.target.value as number }))}
                  label="Duration"
                >
                  {durations.map((d) => (
                    <MenuItem key={d.value} value={d.value}>
                      {d.label}
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
                onChange={(e) => setFormData((prev) => ({ ...prev, notes: e.target.value }))}
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
                  <Typography variant="body1">{displayMentorName}</Typography>
                </Grid>

                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Date & Time
                  </Typography>
                  <Typography variant="body1">
                    {formData.date && formData.time
                      ? `${format(formData.date, 'MMM dd, yyyy')} at ${format(formData.time, 'HH:mm')}`
                      : '-'}
                  </Typography>
                </Grid>

                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Duration
                  </Typography>
                  <Typography variant="body1">{formData.duration} minutes</Typography>
                </Grid>

                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Session Type
                  </Typography>
                  <Typography variant="body1">
                    {sessionTypes.find((t) => t.value === formData.sessionType)?.label || '-'}
                  </Typography>
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">
                    Total Price
                  </Typography>
                  {totalPrice !== null ? (
                    <Typography variant="h6" color="primary">
                      ${totalPrice.toFixed(2)}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      Price will be shown before confirmation
                    </Typography>
                  )}
                </Grid>
              </Grid>
            </Box>

            {formData.notes ? (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Notes
                </Typography>
                <Typography variant="body2">{formData.notes}</Typography>
              </Box>
            ) : null}
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Typography variant="h5">
          Book Session with {displayMentorName}
        </Typography>
      </DialogTitle>

      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : null}

        {renderStepContent(activeStep)}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={submitting}>
          Cancel
        </Button>

        <Box sx={{ flex: '1 1 auto' }} />

        {activeStep > 0 ? (
          <Button onClick={handleBack} disabled={submitting}>
            Back
          </Button>
        ) : null}

        {activeStep < steps.length - 1 ? (
          <Button variant="contained" onClick={handleNext} disabled={isNextDisabled}>
            Next
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={18} /> : null}
          >
            {submitting ? 'Booking...' : 'Confirm Booking'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default BookingDialog;
