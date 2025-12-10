import React, { useState } from 'react';
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
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ContentCopy as CopyIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';

interface TimeSlot {
  id: string;
  start: string;
  end: string;
}

interface DayAvailability {
  day: string;
  enabled: boolean;
  slots: TimeSlot[];
}

const MentorAvailabilityPage: React.FC = () => {
  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  
  const [availability, setAvailability] = useState<DayAvailability[]>(
    daysOfWeek.map(day => ({
      day,
      enabled: day !== 'Saturday' && day !== 'Sunday',
      slots: day !== 'Saturday' && day !== 'Sunday' ? [
        { id: `${day}-1`, start: '09:00', end: '12:00' },
        { id: `${day}-2`, start: '14:00', end: '17:00' },
      ] : [],
    }))
  );

  const handleToggleDay = (day: string) => {
    setAvailability(availability.map(dayAvail =>
      dayAvail.day === day
        ? { ...dayAvail, enabled: !dayAvail.enabled }
        : dayAvail
    ));
  };

  const handleAddSlot = (day: string) => {
    setAvailability(availability.map(dayAvail =>
      dayAvail.day === day
        ? {
            ...dayAvail,
            slots: [...dayAvail.slots, { id: `${day}-${Date.now()}`, start: '09:00', end: '17:00' }],
          }
        : dayAvail
    ));
  };

  const handleRemoveSlot = (day: string, slotId: string) => {
    setAvailability(availability.map(dayAvail =>
      dayAvail.day === day
        ? { ...dayAvail, slots: dayAvail.slots.filter(slot => slot.id !== slotId) }
        : dayAvail
    ));
  };

  const handleUpdateSlot = (day: string, slotId: string, field: 'start' | 'end', value: string) => {
    setAvailability(availability.map(dayAvail =>
      dayAvail.day === day
        ? {
            ...dayAvail,
            slots: dayAvail.slots.map(slot =>
              slot.id === slotId ? { ...slot, [field]: value } : slot
            ),
          }
        : dayAvail
    ));
  };

  const handleCopyWeek = () => {
    // Placeholder: copy current week to next week
    alert('Availability copied to next week');
  };

  const handleClearAll = () => {
    if (window.confirm('Are you sure you want to clear all availability?')) {
      setAvailability(availability.map(dayAvail => ({ ...dayAvail, slots: [] })));
    }
  };

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
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
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
      </Box>

      {/* Weekly Availability */}
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
                    {dayAvail.slots.map((slot) => (
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
                    ))}
                    <Button
                      variant="outlined"
                      startIcon={<AddIcon />}
                      onClick={() => handleAddSlot(dayAvail.day)}
                      fullWidth
                      size="small"
                    >
                      Add Time Slot
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Save Button */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
        <Button
          variant="contained"
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
            },
          }}
        >
          Save Availability
        </Button>
      </Box>
    </Box>
  );
};

export default MentorAvailabilityPage;

