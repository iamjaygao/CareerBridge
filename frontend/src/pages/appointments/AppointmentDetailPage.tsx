import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Rating,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon, Edit as EditIcon, Cancel as CancelIcon } from '@mui/icons-material';
import { format } from 'date-fns';

import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import { useNotification } from '../../components/common/NotificationProvider';
import appointmentService from '../../services/api/appointmentService';

const getStatusLabel = (status: string): string => {
  const statusMap: { [key: string]: string } = {
    pending: 'Pending Payment',
    confirmed: 'Confirmed',
    expired: 'Expired',
    cancelled: 'Cancelled',
    completed: 'Completed',
  };
  return statusMap[status] || status.charAt(0).toUpperCase() + status.slice(1);
};

const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
  switch (status) {
    case 'pending':
      return 'warning';
    case 'confirmed':
      return 'success';
    case 'expired':
    case 'cancelled':
      return 'error';
    case 'completed':
      return 'info';
    default:
      return 'default';
  }
};

const AppointmentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { showSuccess, showError } = useNotification();
  const [appointment, setAppointment] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [cancelling, setCancelling] = useState(false);
  const [ratingValue, setRatingValue] = useState<number | null>(0);
  const [feedback, setFeedback] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const reviewSectionRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (id) {
      fetchAppointment();
    }
  }, [id]);

  const fetchAppointment = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      setError(null);
      const data = await appointmentService.getAppointmentById(parseInt(id));
      setAppointment(data);
      setRatingValue(data?.user_rating || 0);
      setFeedback(data?.user_feedback || '');
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to load appointment');
    } finally {
      setLoading(false);
    }
  };

  const handleCompletePayment = () => {
    if (appointment?.id) {
      navigate(`/student/appointments/${appointment.id}`);
    }
  };

  const handleCancel = async () => {
    if (!appointment?.id) return;
    
    try {
      setCancelling(true);
      await appointmentService.lockSlot({
        appointment_id: appointment.id,
        action: 'cancel',
        cancel_reason: cancelReason,
      });
      showSuccess('Appointment cancelled successfully');
      setCancelDialogOpen(false);
      setCancelReason('');
      fetchAppointment();
    } catch (err: any) {
      showError(err?.response?.data?.error || 'Failed to cancel appointment');
    } finally {
      setCancelling(false);
    }
  };

  const handleReschedule = () => {
    if (appointment?.id) {
      navigate(`/student/appointments/${appointment.id}/reschedule`);
    }
  };

  const handleSubmitReview = async () => {
    if (!appointment?.id) return;
    if (!ratingValue || ratingValue < 1) {
      showError('Please provide a rating before submitting.');
      return;
    }
    try {
      setSubmittingReview(true);
      await appointmentService.rateAppointment(appointment.id, ratingValue, feedback);
      showSuccess('Thanks for your feedback!');
      await fetchAppointment();
    } catch (err: any) {
      showError(err?.response?.data?.error || 'Failed to submit feedback.');
    } finally {
      setSubmittingReview(false);
    }
  };

  const isFuture = appointment?.scheduled_start 
    ? new Date(appointment.scheduled_start) > new Date()
    : false;
  
  const canCancel = (appointment?.status === 'pending' || appointment?.status === 'confirmed') && isFuture;
  const canReschedule = appointment?.status === 'confirmed' && isFuture;
  const needsReview = appointment?.status === 'completed' && !appointment?.user_rating && !appointment?.user_feedback;
  const reviewRequested = new URLSearchParams(location.search).get('review') === 'true';

  useEffect(() => {
    if ((needsReview || reviewRequested) && reviewSectionRef.current) {
      reviewSectionRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [needsReview, reviewRequested]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  if (!appointment) {
    return <ErrorAlert message="Appointment not found" />;
  }

  const scheduledStart = new Date(appointment.scheduled_start);
  const scheduledEnd = new Date(appointment.scheduled_end);
  const durationMinutes = Math.round((scheduledEnd.getTime() - scheduledStart.getTime()) / (1000 * 60));
  
  const mentorName = appointment.mentor?.user
    ? `${appointment.mentor.user.first_name || ''} ${appointment.mentor.user.last_name || ''}`.trim() || appointment.mentor.user.username
    : 'Mentor';

  const priceDisplay = appointment.price
    ? `$${parseFloat(appointment.price).toFixed(2)} ${appointment.currency || 'USD'}`
    : 'N/A';

  return (
    <>
      <PageHeader
        title="Appointment Details"
        breadcrumbs={[
          { label: 'Appointments', path: '/student/appointments' },
          { label: 'Details', path: `/student/appointments/${id}` }
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
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Appointment Summary
              </Typography>
            </Box>
            {appointment.status === 'pending' && appointment.is_paid === false && (
              <Alert severity="warning" sx={{ mb: 3 }}>
                Payment is pending. Please complete payment to confirm your appointment.
              </Alert>
            )}
            {appointment.status === 'pending' && appointment.is_paid === true && (
              <Alert severity="info" sx={{ mb: 3 }}>
                Payment received. Your appointment is awaiting confirmation.
              </Alert>
            )}

            <Grid container spacing={3}>
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
                  Status
                </Typography>
                <Chip
                  label={getStatusLabel(appointment.status)}
                  color={getStatusColor(appointment.status)}
                  size="small"
                  sx={{ mt: 0.5 }}
                />
              </Grid>

              {appointment.title && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Service
                  </Typography>
                  <Typography variant="body1">
                    {appointment.title}
                  </Typography>
                </Grid>
              )}

              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Date
                </Typography>
                <Typography variant="body1">
                  {format(scheduledStart, 'EEEE, MMMM dd, yyyy')}
                </Typography>
              </Grid>

              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Time
                </Typography>
                <Typography variant="body1">
                  {format(scheduledStart, 'HH:mm')} – {format(scheduledEnd, 'HH:mm')}
                </Typography>
              </Grid>

              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Duration
                </Typography>
                <Typography variant="body1">
                  {durationMinutes} minutes
                </Typography>
              </Grid>

              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Price
                </Typography>
                <Typography variant="body1" color="primary" fontWeight="bold">
                  {priceDisplay}
                </Typography>
              </Grid>
            </Grid>

            <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
              {appointment.status === 'pending' && appointment.is_paid === false && (
                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  onClick={handleCompletePayment}
                >
                  Complete Payment
                </Button>
              )}
              
              {canReschedule && (
                <Button
                  variant="outlined"
                  color="primary"
                  size="large"
                  startIcon={<EditIcon />}
                  onClick={handleReschedule}
                >
                  Reschedule
                </Button>
              )}
              
              {canCancel && (
                <Button
                  variant="outlined"
                  color="error"
                  size="large"
                  startIcon={<CancelIcon />}
                  onClick={() => setCancelDialogOpen(true)}
                >
                  Cancel Appointment
                </Button>
              )}
            </Box>

            {appointment.status === 'completed' && (
              <Box ref={reviewSectionRef} sx={{ mt: 4 }}>
                <Typography variant="h6" gutterBottom>
                  Session Feedback
                </Typography>
                {appointment.user_rating || appointment.user_feedback ? (
                  <Box>
                    <Rating value={Number(appointment.user_rating || 0)} readOnly />
                    {appointment.user_feedback && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {appointment.user_feedback}
                      </Typography>
                    )}
                  </Box>
                ) : (
                  <>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Share your experience to help improve future sessions.
                    </Typography>
                    <Rating
                      value={ratingValue}
                      onChange={(_, value) => setRatingValue(value)}
                      sx={{ mb: 2 }}
                    />
                    <TextField
                      fullWidth
                      multiline
                      minRows={3}
                      label="Feedback (optional)"
                      value={feedback}
                      onChange={(event) => setFeedback(event.target.value)}
                      sx={{ mb: 2 }}
                    />
                    <Button
                      variant="contained"
                      onClick={handleSubmitReview}
                      disabled={submittingReview}
                    >
                      {submittingReview ? 'Submitting...' : 'Submit Feedback'}
                    </Button>
                  </>
                )}
              </Box>
            )}
            {appointment.status !== 'completed' && reviewRequested && (
              <Alert severity="info" sx={{ mt: 3 }}>
                This session is not completed yet. You can leave feedback once it is finished.
              </Alert>
            )}
          </CardContent>
        </Card>
      </Container>

      {/* Cancel Confirmation Dialog */}
      <Dialog
        open={cancelDialogOpen}
        onClose={() => !cancelling && setCancelDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Cancel Appointment</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to cancel this appointment? This action cannot be undone.
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Reason (Optional)"
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            placeholder="Please let us know why you're cancelling..."
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => {
              setCancelDialogOpen(false);
              setCancelReason('');
            }}
            disabled={cancelling}
          >
            Keep Appointment
          </Button>
          <Button
            onClick={handleCancel}
            color="error"
            variant="contained"
            disabled={cancelling}
          >
            {cancelling ? 'Cancelling...' : 'Cancel Appointment'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default AppointmentDetailPage;
