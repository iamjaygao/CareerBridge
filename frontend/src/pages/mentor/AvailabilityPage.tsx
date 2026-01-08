import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  TextField,
  IconButton,
  Chip,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ContentCopy as CopyIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import appointmentService from '../../services/api/appointmentService';
import mentorService from '../../services/api/mentorService';

interface TimeSlot {
  id: string;
  backendId?: number;
  start: string;
  end: string;
}

interface DayAvailability {
  day: string;
  date: string;
  enabled: boolean;
  slots: TimeSlot[];
}

const MentorAvailabilityPage: React.FC = () => {
  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [onboardingMessage, setOnboardingMessage] = useState<string | null>(null);
  const [mentorId, setMentorId] = useState<number | null>(null);
  const [slotPrice, setSlotPrice] = useState<number>(0);
  const [availability, setAvailability] = useState<DayAvailability[]>([]);
  const [removedSlotIds, setRemovedSlotIds] = useState<number[]>([]);
  const [weekRange, setWeekRange] = useState<{ start: Date; end: Date } | null>(null);
  const [weekOffset, setWeekOffset] = useState(0);
  const [openClearConfirm, setOpenClearConfirm] = useState(false);
  const normalizeArray = <T,>(value: any, fallbackKeys: string[] = []): T[] => {
    if (Array.isArray(value)) return value;
    for (const key of fallbackKeys) {
      if (Array.isArray(value?.[key])) return value[key];
    }
    return [];
  };

  const formatDate = (date: Date) => {
    const yyyy = date.getFullYear();
    const mm = `${date.getMonth() + 1}`.padStart(2, '0');
    const dd = `${date.getDate()}`.padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  };

  const getWeekStart = (date: Date) => {
    const day = date.getDay();
    const diff = day === 0 ? -6 : 1 - day;
    const start = new Date(date);
    start.setDate(date.getDate() + diff);
    start.setHours(0, 0, 0, 0);
    return start;
  };

  const formatTime = (value: string) => {
    const dt = new Date(value);
    return dt.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
  };

  const formatWeekRange = (start: Date, end: Date) => {
    const options: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };
    const yearOptions: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric', year: 'numeric' };
    const sameYear = start.getFullYear() === end.getFullYear();
    const startLabel = start.toLocaleDateString('en-US', sameYear ? options : yearOptions);
    const endLabel = end.toLocaleDateString('en-US', yearOptions);
    return `${startLabel} – ${endLabel}`;
  };

  const isMorning = (timeValue: string) => {
    const [hour] = timeValue.split(':').map((value) => Number(value));
    return hour < 12;
  };

  useEffect(() => {
    const fetchAvailability = async () => {
      try {
        setError(null);
        setOnboardingMessage(null);
        
        // Step 1: Check mentor profile status (READ-ONLY endpoint)
        const profileStatus = await mentorService.getMyProfile();
        
        if (!profileStatus?.has_profile) {
          // This is an ONBOARDING STATE, not an error
          setOnboardingMessage('Please create your mentor profile before setting availability.');
          setLoading(false);
          return;
        }
        
        const mentorProfileId = profileStatus.mentor_profile_id;
        if (!mentorProfileId) {
          // This is a real data error
          setError('Mentor profile data is incomplete. Please contact support.');
          setLoading(false);
          return;
        }
        
        // Step 2: Check Stripe Connect status (READ-ONLY endpoint)
        const connectStatus = await mentorService.getConnectStatus();
        
        if (!connectStatus?.is_connected) {
          // This is an ONBOARDING STATE, not an error
          setOnboardingMessage('Please complete Stripe Connect onboarding before setting availability. This is required to receive payments from students.');
          setLoading(false);
          return;
        }
        
        // Step 3: Check payout status (READ-ONLY endpoint)
        const payoutStatus = await mentorService.getPayoutStatus();
        
        if (!payoutStatus?.payout_enabled) {
          // This is an ONBOARDING STATE, not an error
          setOnboardingMessage('Payouts are not enabled yet. Please complete your Stripe account setup.');
          setLoading(false);
          return;
        }
        
        // All checks passed - proceed with loading availability
        setMentorId(mentorProfileId);

        const servicesResponse = await mentorService.getMyServices(mentorProfileId);
        const services = normalizeArray<any>(servicesResponse, ['results', 'services']);
        const primaryService = services[0] ?? null;
         
        const price = primaryService?.price_per_hour || primaryService?.fixed_price || 0;
        setSlotPrice(Number(price));

        const startDate = getWeekStart(new Date());
        startDate.setDate(startDate.getDate() + weekOffset * 7);
        const endDate = new Date(startDate);
        endDate.setDate(startDate.getDate() + 6);
        setWeekRange({ start: startDate, end: endDate });

        const slots = await appointmentService.getMentorTimeSlots({
          mentor_id: mentorProfileId,
          from: formatDate(startDate),
          to: formatDate(endDate),
        });

        const dayMap: DayAvailability[] = daysOfWeek.map((day, index) => {
          const date = new Date(startDate);
          date.setDate(startDate.getDate() + index);
          return {
            day,
            date: formatDate(date),
            enabled: false,
            slots: [],
          };
        });

        slots.forEach((slot: any) => {
          const slotDate = formatDate(new Date(slot.start_time));
          const dayEntry = dayMap.find((entry) => entry.date === slotDate);
          if (!dayEntry) return;
          dayEntry.enabled = true;
          dayEntry.slots.push({
            id: `${dayEntry.day}-${slot.id}`,
            backendId: slot.id,
            start: formatTime(slot.start_time),
            end: formatTime(slot.end_time),
          });
        });

        setAvailability(dayMap);
      } catch {
        setError('Failed to load availability.');
      } finally {
        setLoading(false);
      }
    };

    fetchAvailability();
  }, [weekOffset]);

  const handleToggleDay = (day: string) => {
    setAvailability(availability.map(dayAvail => {
      if (dayAvail.day !== day) return dayAvail;
      if (dayAvail.enabled) {
        const idsToRemove = dayAvail.slots.filter((slot) => slot.backendId).map((slot) => slot.backendId!);
        if (idsToRemove.length) {
          setRemovedSlotIds((prev) => [...prev, ...idsToRemove]);
        }
        return { ...dayAvail, enabled: false, slots: [] };
      }
      return { ...dayAvail, enabled: true };
    }));
  };

  const handleAddSlotForPeriod = (day: string, period: 'Morning' | 'Afternoon') => {
    const baseStart = period === 'Morning' ? '09:00' : '12:00';
    const baseEnd = period === 'Morning' ? '10:00' : '13:00';
    setAvailability(availability.map(dayAvail => {
      if (dayAvail.day !== day) return dayAvail;
      const periodSlots = dayAvail.slots.filter((slot) =>
        period === 'Morning' ? isMorning(slot.start) : !isMorning(slot.start)
      );
      if (!periodSlots.length) {
        return {
          ...dayAvail,
          slots: [
            ...dayAvail.slots,
            { id: `${day}-${period}-${Date.now()}`, start: baseStart, end: baseEnd },
          ],
        };
      }
      const toMinutes = (timeValue: string) => {
        const [hour, minute] = timeValue.split(':').map((value) => Number(value));
        return (hour || 0) * 60 + (minute || 0);
      };
      const toTimeString = (totalMinutes: number) => {
        const hours = Math.floor(totalMinutes / 60);
        const minutes = totalMinutes % 60;
        return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
      };
      const sorted = [...periodSlots].sort((a, b) => toMinutes(a.start) - toMinutes(b.start));
      const last = sorted[sorted.length - 1];
      const lastEnd = toMinutes(last.end);
      const nextStart = toTimeString(lastEnd);
      const nextEnd = toTimeString(lastEnd + 60);
      const exists = dayAvail.slots.some((slot) => slot.start === nextStart && slot.end === nextEnd);
      if (exists) {
        return dayAvail;
      }
      return {
        ...dayAvail,
        slots: [
          ...dayAvail.slots,
          { id: `${day}-${period}-${Date.now()}`, start: nextStart, end: nextEnd },
        ],
      };
    }));
  };

  const handleRemoveSlot = (day: string, slotId: string) => {
    setAvailability(availability.map(dayAvail =>
      dayAvail.day === day
        ? {
            ...dayAvail,
            slots: dayAvail.slots.filter(slot => {
              if (slot.id === slotId && slot.backendId) {
                setRemovedSlotIds((prev) => [...prev, slot.backendId!]);
              }
              return slot.id !== slotId;
            }),
          }
        : dayAvail
    ));
  };

  const handleUpdateSlot = (day: string, slotId: string, field: 'start' | 'end', value: string) => {
    setAvailability(availability.map(dayAvail =>
      dayAvail.day === day
        ? {
            ...dayAvail,
            slots: dayAvail.slots.map(slot =>
              slot.id === slotId
                ? {
                    ...slot,
                    [field]: value,
                    backendId: slot.backendId ? undefined : slot.backendId,
                  }
                : slot
            ),
          }
        : dayAvail
    ));
    const targetSlot = availability
      .find((entry) => entry.day === day)
      ?.slots.find((slot) => slot.id === slotId);
    if (targetSlot?.backendId) {
      setRemovedSlotIds((prev) => [...prev, targetSlot.backendId!]);
    }
  };

  const handleCopyWeek = () => {
    if (!mentorId) return;
    const nextWeekSlots = availability.flatMap((dayAvail) => {
      if (!dayAvail.enabled) {
        return [];
      }
      const date = new Date(dayAvail.date);
      date.setDate(date.getDate() + 7);
      const newDate = formatDate(date);
      return dayAvail.slots.map((slot) => ({
        start: new Date(`${newDate}T${slot.start}`),
        end: new Date(`${newDate}T${slot.end}`),
      }));
    });

    if (!nextWeekSlots.length) {
      setSuccess('No availability to copy.');
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);
    Promise.all(
      nextWeekSlots.map((slot) =>
        appointmentService.createTimeSlot({
          start_time: slot.start.toISOString(),
          end_time: slot.end.toISOString(),
          is_available: true,
          price: slotPrice,
          currency: 'USD',
        })
      )
    )
      .then(() => {
        setSuccess('Availability copied to next week.');
      })
      .catch((err: any) => {
        const message =
          err?.response?.data?.detail ||
          err?.response?.data?.non_field_errors?.[0] ||
          'Failed to copy availability.';
        setError(message);
      })
      .finally(() => {
        setSaving(false);
      });
  };

  const handleClearAll = () => {
    // Open confirmation dialog instead of using window.confirm
    setOpenClearConfirm(true);
  };

  const handleConfirmClear = () => {
    // Perform the actual clear logic
    const idsToRemove = availability.flatMap((dayAvail) =>
      dayAvail.slots.filter((slot) => slot.backendId).map((slot) => slot.backendId!)
    );
    if (idsToRemove.length) {
      setRemovedSlotIds((prev) => [...prev, ...idsToRemove]);
    }
    setAvailability(availability.map(dayAvail => ({ ...dayAvail, enabled: false, slots: [] })));
    
    // Close the dialog
    setOpenClearConfirm(false);
  };

  const handleCancelClear = () => {
    // Close dialog without side effects
    setOpenClearConfirm(false);
  };

  const handleSave = async () => {
    if (!mentorId) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const now = new Date();
      const removed = Array.from(new Set(removedSlotIds));
      await Promise.all(
        removed.map((slotId) => appointmentService.updateTimeSlot(slotId, { is_available: false }))
      );
      setRemovedSlotIds([]);

      const newSlots = availability.flatMap((dayAvail) =>
        dayAvail.enabled
          ? dayAvail.slots.filter((slot) => !slot.backendId).map((slot) => ({
              date: dayAvail.date,
              start: slot.start,
              end: slot.end,
            }))
          : []
      );

      for (const slot of newSlots) {
        const startTime = new Date(`${slot.date}T${slot.start}`);
        const endTime = new Date(`${slot.date}T${slot.end}`);
        if (startTime <= now) {
          continue;
        }
        await appointmentService.createTimeSlot({
          start_time: startTime.toISOString(),
          end_time: endTime.toISOString(),
          is_available: true,
          price: slotPrice,
          currency: 'USD',
        });
      }

      setSuccess('Availability saved.');
    } catch (err: any) {
      const message =
        err?.response?.data?.detail ||
        err?.response?.data?.non_field_errors?.[0] ||
        'Failed to save availability.';
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading availability..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            Availability
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Set your weekly availability for student bookings
          </Typography>
          {weekRange && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {formatWeekRange(weekRange.start, weekRange.end)}
            </Typography>
          )}
          {/* Onboarding messages (warning, not error) */}
          {onboardingMessage && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              {onboardingMessage}
            </Alert>
          )}
          {/* Real errors (e.g., network failures, data issues) */}
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
          {success && (
            <Alert severity="success" sx={{ mt: 2 }}>
              {success}
            </Alert>
          )}
        </Box>
        {/* Availability controls - disabled during onboarding */}
        {!onboardingMessage && (
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="outlined"
              onClick={() => setWeekOffset((prev) => Math.max(0, prev - 1))}
              disabled={weekOffset === 0}
            >
              This Week
            </Button>
            <Button
              variant="outlined"
              onClick={() => setWeekOffset((prev) => Math.min(3, prev + 1))}
              disabled={weekOffset >= 3}
            >
              Next Week
            </Button>
            <Button
              variant="outlined"
              startIcon={<CopyIcon />}
              onClick={handleCopyWeek}
            >
              Copy to Next Week
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<ClearIcon />}
              onClick={handleClearAll}
            >
              Clear All
            </Button>
          </Box>
        )}
      </Box>

      {/* Weekly Availability - hidden during onboarding */}
      {!onboardingMessage && (
      <Grid container spacing={3}>
        {availability.map((dayAvail) => (
          <Grid item xs={12} md={6} key={dayAvail.day}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {dayAvail.day}
                  </Typography>
                  <Chip
                    label={dayAvail.enabled ? 'Available' : 'Unavailable'}
                    color={dayAvail.enabled ? 'success' : 'default'}
                    onClick={() => handleToggleDay(dayAvail.day)}
                    sx={{ cursor: 'pointer' }}
                  />
                </Box>
                {dayAvail.enabled && (
                  <>
                    <Divider sx={{ mb: 2 }} />
                    {(['Morning', 'Afternoon'] as const).map((period) => {
                      const slots = dayAvail.slots.filter((slot) =>
                        period === 'Morning' ? isMorning(slot.start) : !isMorning(slot.start)
                      );
                      return (
                        <Box key={period} sx={{ mb: 2 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                            <Typography variant="subtitle2" color="text.secondary">
                              {period}
                            </Typography>
                            <Button
                              variant="outlined"
                              size="small"
                              startIcon={<AddIcon />}
                              onClick={() => handleAddSlotForPeriod(dayAvail.day, period)}
                            >
                              Add Time Slot
                            </Button>
                          </Box>
                          {slots.length ? (
                            slots.map((slot) => (
                              <Box
                                key={slot.id}
                                sx={{
                                  display: 'flex',
                                  gap: 1,
                                  mb: 2,
                                  alignItems: 'center',
                                }}
                              >
                                <TextField
                                  type="time"
                                  label="Start"
                                  value={slot.start}
                                  onChange={(e) => handleUpdateSlot(dayAvail.day, slot.id, 'start', e.target.value)}
                                  size="small"
                                  InputLabelProps={{ shrink: true }}
                                />
                                <TextField
                                  type="time"
                                  label="End"
                                  value={slot.end}
                                  onChange={(e) => handleUpdateSlot(dayAvail.day, slot.id, 'end', e.target.value)}
                                  size="small"
                                  InputLabelProps={{ shrink: true }}
                                />
                                <IconButton
                                  color="error"
                                  onClick={() => handleRemoveSlot(dayAvail.day, slot.id)}
                                  size="small"
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </Box>
                            ))
                          ) : (
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                              No slots set for this period.
                            </Typography>
                          )}
                        </Box>
                      );
                    })}
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      )}

      {/* Save Button - hidden during onboarding */}
      {!onboardingMessage && (
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
        <Button
          variant="contained"
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
            },
          }}
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Availability'}
        </Button>
      </Box>
      )}

      {/* Clear Availability Confirmation Dialog */}
      <Dialog
        open={openClearConfirm}
        onClose={handleCancelClear}
        aria-labelledby="clear-dialog-title"
        aria-describedby="clear-dialog-description"
      >
        <DialogTitle id="clear-dialog-title">
          Clear availability?
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="clear-dialog-description">
            This will remove all your availability slots for the selected week.
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelClear} variant="outlined">
            Cancel
          </Button>
          <Button onClick={handleConfirmClear} variant="contained" color="error" autoFocus>
            Clear Availability
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MentorAvailabilityPage;
