import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Button,
  Typography,
  Avatar,
  Box,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Rating,
  TextField,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  VideoCall as VideoCallIcon,
  Schedule as ScheduleIcon,
  Edit as EditIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../store';
import { cancelAppointment, submitFeedback } from '../../store/slices/appointmentSlice';
import { Appointment } from '../../types';

interface AppointmentCardProps {
  appointment: Appointment;
  onReschedule?: (appointmentId: number) => void;
}

const AppointmentCard: React.FC<AppointmentCardProps> = ({
  appointment,
  onReschedule,
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const [feedbackDialogOpen, setFeedbackDialogOpen] = useState(false);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [rating, setRating] = useState<number | null>(null);
  const [comment, setComment] = useState('');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'success';
      case 'pending':
        return 'warning';
      case 'cancelled':
        return 'error';
      case 'completed':
        return 'info';
      default:
        return 'default';
    }
  };

  const handleCancelAppointment = async () => {
    try {
      await dispatch(cancelAppointment(appointment.id)).unwrap();
      setCancelDialogOpen(false);
    } catch (error) {
      console.error('Failed to cancel appointment:', error);
    }
  };

  const handleSubmitFeedback = async () => {
    if (rating) {
      try {
        await dispatch(
          submitFeedback({
            id: appointment.id,
            feedback: { rating, comment },
          })
        ).unwrap();
        setFeedbackDialogOpen(false);
      } catch (error) {
        console.error('Failed to submit feedback:', error);
      }
    }
  };

  const canJoinMeeting = appointment.status === 'confirmed' && appointment.meeting_link;
  const canCancel = appointment.status === 'pending' || appointment.status === 'confirmed';
  const canReschedule = appointment.status === 'pending' || appointment.status === 'confirmed';
  const canLeaveFeedback = appointment.status === 'completed' && !appointment.user_feedback;

  return (
    <>
      <Card
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          transition: 'transform 0.2s',
          '&:hover': {
            transform: 'translateY(-4px)',
          },
        }}
      >
        <CardContent sx={{ flexGrow: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Avatar
              src={appointment.mentor.user.avatar}
              sx={{
                width: 48,
                height: 48,
                mr: 2,
                border: '2px solid',
                borderColor: 'primary.main',
              }}
            />
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h6">
                {`${appointment.mentor.user.first_name} ${appointment.mentor.user.last_name}`}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {appointment.mentor.current_position}
              </Typography>
            </Box>
            <Chip
              label={appointment.status}
              color={getStatusColor(appointment.status)}
              size="small"
            />
          </Box>

          <Typography variant="subtitle1" gutterBottom>
            {appointment.title}
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <ScheduleIcon fontSize="small" sx={{ mr: 1, color: 'action.active' }} />
            <Typography variant="body2" color="text.secondary">
              {appointment.scheduled_start
                ? new Date(appointment.scheduled_start).toLocaleString()
                : ''}
              {' - '}
              {appointment.scheduled_end
                ? new Date(appointment.scheduled_end).toLocaleTimeString()
                : ''}
            </Typography>
          </Box>

          {appointment.meeting_platform && (
            <Typography variant="body2" color="text.secondary">
              Meeting Platform: {appointment.meeting_platform}
            </Typography>
          )}

          {appointment.user_feedback && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Your Feedback:
              </Typography>
              {appointment.user_rating && (
                <Rating value={appointment.user_rating} readOnly size="small" sx={{ mb: 1 }} />
              )}
              <Typography variant="body2" color="text.secondary">
                {appointment.user_feedback}
              </Typography>
            </Box>
          )}
        </CardContent>

        <CardActions sx={{ justifyContent: 'flex-end', p: 2 }}>
          {canJoinMeeting && appointment.meeting_link && (
            <Tooltip title="Join Meeting">
              <IconButton
                color="primary"
                component="a"
                href={appointment.meeting_link}
                target="_blank"
              >
                <VideoCallIcon />
              </IconButton>
            </Tooltip>
          )}

          {canReschedule && onReschedule && (
            <Tooltip title="Reschedule">
              <IconButton
                color="primary"
                onClick={() => onReschedule(appointment.id)}
              >
                <EditIcon />
              </IconButton>
            </Tooltip>
          )}

          {canCancel && (
            <Tooltip title="Cancel">
              <IconButton
                color="error"
                onClick={() => setCancelDialogOpen(true)}
              >
                <CancelIcon />
              </IconButton>
            </Tooltip>
          )}

          {canLeaveFeedback && (
            <Button
              size="small"
              variant="outlined"
              onClick={() => setFeedbackDialogOpen(true)}
            >
              Leave Feedback
            </Button>
          )}
        </CardActions>
      </Card>

      {/* Feedback Dialog */}
      <Dialog
        open={feedbackDialogOpen}
        onClose={() => setFeedbackDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Leave Feedback</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <Typography>How was your session?</Typography>
            <Rating
              value={rating}
              onChange={(event, newValue) => setRating(newValue)}
              size="large"
            />
            <TextField
              label="Comments"
              multiline
              rows={4}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFeedbackDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSubmitFeedback}
            variant="contained"
            disabled={!rating}
          >
            Submit
          </Button>
        </DialogActions>
      </Dialog>

      {/* Cancel Dialog */}
      <Dialog
        open={cancelDialogOpen}
        onClose={() => setCancelDialogOpen(false)}
      >
        <DialogTitle>Cancel Appointment</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to cancel this appointment? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialogOpen(false)}>No, Keep It</Button>
          <Button onClick={handleCancelAppointment} color="error" variant="contained">
            Yes, Cancel
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default AppointmentCard;