import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Avatar,
  Rating,
  Chip,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
} from '@mui/material';
import {
  Work as WorkIcon,
  Business as BusinessIcon,
  Verified as VerifiedIcon,
  Event as EventIcon,
  AttachMoney as MoneyIcon,
} from '@mui/icons-material';
import { format, parseISO, addDays } from 'date-fns';

import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import { useNotification } from '../../components/common/NotificationProvider';
import mentorService from '../../services/api/mentorService';
import { sessionService } from '../../services/api/sessionService';


/* =====================
   Types
===================== */

interface MentorDetail {
  id: number;
  user: {
    first_name: string;
    last_name: string;
    avatar?: string;
  };
  bio: string;
  years_of_experience: number;
  current_position: string;
  industry: string;
  average_rating: number;
  total_reviews: number;
  total_sessions: number;
  total_earnings: number;
  is_verified: boolean;
  specializations: string[];
  services: MentorService[];
  reviews: MentorReview[];
  availability: MentorAvailability[];
  mentor_card?: {
    line1: string;
    line2?: string;
  };
  rating?: number | null;
  review_count?: number;
  trust_label?: string | null;
  cta_label?: string;
  ranking_reason?: string;
  primary_service_id?: number;
}

interface MentorService {
  id: number;
  title: string;
  description: string;
  service_type: string;
  duration_minutes: number;
  display_price: string;
  is_active?: boolean;
}

interface MentorReview {
  id: number;
  rating: number;
  comment: string;
  created_at: string;
  user: {
    username: string;
  };
}

interface MentorAvailability {
  id: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
}

interface BookingForm {
  service_id: number;
  scheduled_date: Date | null;
  scheduled_time: string;
  user_notes: string;
  duration_minutes?: number;
}

/* =====================
   Component
===================== */

const MentorDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();

  const [mentor, setMentor] = useState<MentorDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [tabValue, setTabValue] = useState(0);
  const [bookingDialogOpen, setBookingDialogOpen] = useState(false);
  const [selectedServiceId, setSelectedServiceId] = useState<number | null>(null);

  const [availableSlots, setAvailableSlots] = useState<
    { start_time: string; end_time: string; duration_minutes: number }[]
  >([]);
  const [loadingSlots, setLoadingSlots] = useState(false);

  const [bookingForm, setBookingForm] = useState<BookingForm>({
    service_id: 0,
    scheduled_date: null,
    scheduled_time: '',
    user_notes: '',
  });

  /* =====================
     Data Fetch
  ===================== */

  const fetchMentorDetails = useCallback(async () => {
    try {
      setLoading(true);
      const data = await mentorService.getMentorById(Number(id));
      setMentor(data);
    } catch {
      setError('Failed to load mentor details');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) fetchMentorDetails();
  }, [id, fetchMentorDetails]);

  // Determine primary service on mentor data load
  useEffect(() => {
    if (mentor) {
      const mentorServices = mentor.services ?? [];
      const activeServices = mentorServices.filter(s => s.is_active !== false);
      if (activeServices.length > 0 && selectedServiceId === null) {
        // Strict defaulting: prefer primary_service_id if present AND exists in activeServices
        const primaryServiceId = mentor.primary_service_id;
        const primaryServiceInActive = primaryServiceId
          ? activeServices.find(s => s.id === primaryServiceId)
          : null;
        
        // Use primary_service_id if valid, otherwise fallback to first active service
        const defaultService = primaryServiceInActive || activeServices[0];
        if (defaultService) {
          setSelectedServiceId(defaultService.id);
        }
      }
    }
  }, [mentor, selectedServiceId]);

  /* =====================
     Booking Helpers
  ===================== */

  const fetchAvailableSlots = async (date: Date, serviceId: number) => {
    if (!mentor) return;
    try {
      setLoadingSlots(true);
      const slots = await mentorService.getMentorAvailability(
        mentor.id,
        format(date, 'yyyy-MM-dd'),
        serviceId
      );
      setAvailableSlots(slots);
    } catch {
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleServiceContinue = (service: MentorService) => {
    // Directly open booking dialog instead of showing availability tab
    handleServiceSelect(service);
  };

  const handleServiceSelect = (service: MentorService) => {
    setBookingForm({
      service_id: service.id,
      duration_minutes: service.duration_minutes,
      scheduled_date: null,
      scheduled_time: '',
      user_notes: '',
    });
    setBookingDialogOpen(true);
  };

  const handleBookingSubmit = async () => {
    if (!mentor || !bookingForm.scheduled_date) return;

    try {
      await sessionService.createSession({
        mentor_id: mentor.id,
        service_id: bookingForm.service_id,
        scheduled_date: format(bookingForm.scheduled_date, 'yyyy-MM-dd'),
        scheduled_time: bookingForm.scheduled_time,
        user_notes: bookingForm.user_notes,
        duration_minutes: bookingForm.duration_minutes,
      });
      showSuccess('Session booked successfully!');
      setBookingDialogOpen(false);
      navigate('/student/appointments');
    } catch {
      showError('Failed to book session');
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error || !mentor) return <ErrorAlert message={error || 'Mentor not found'} />;
  if (mentor) {
    (window as any).__MENTOR__ = mentor;
  }
  // Safe local defaults to prevent crashes
  const services = mentor.services ?? [];
  const reviews = mentor.reviews ?? [];
  const specializations = mentor.specializations ?? [];
  
  // Filter active services only
  const activeServices = services.filter(s => s.is_active !== false);
  
  if (activeServices.length === 0) {
    return <ErrorAlert message="This mentor has no active services available." />;
  }
  
  // Get primary service: use primary_service_id if present AND exists in activeServices
  const primaryServiceId = mentor.primary_service_id;
  const primaryService = primaryServiceId
    ? activeServices.find(s => s.id === primaryServiceId) || null
    : null;
  
  // Get selected service (defaults to primary if valid, otherwise first active)
  const selectedService = selectedServiceId
    ? activeServices.find(s => s.id === selectedServiceId) || (primaryService || activeServices[0])
    : (primaryService || activeServices[0]);
  
  // Reorder services: primary first (if it exists and is active)
  const orderedServices = primaryService
    ? [primaryService, ...activeServices.filter(s => s.id !== primaryService.id)]
    : activeServices;

  return (
    <>
      <PageHeader
        title={`${mentor.user.first_name} ${mentor.user.last_name}`}
        breadcrumbs={[
          { label: 'Mentors', path: '/student/mentors' },
          { label: mentor.user.first_name, path: `/student/mentors/${mentor.id}` },
        ]}
      />

      <Container maxWidth="lg">
        {/* ===== Hero Section ===== */}
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          {/* 1) Hero Title */}
          {primaryService?.service_type && (
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mb: 1, textTransform: 'uppercase', letterSpacing: '0.5px' }}
            >
              {primaryService.service_type.replace('_', ' ')}
            </Typography>
          )}
          
          {/* 2) Hero Headline */}
          {((mentor as any).hero_headline || mentor.mentor_card?.line1) && (
            <Typography 
              variant="h4" 
              component="h1" 
              sx={{ 
                fontWeight: 700, 
                mb: 2,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {(mentor as any).hero_headline}
            </Typography>
          )}
          
          {/* 3) Hero Subline */}
          {((mentor as any).hero_subline || mentor.mentor_card?.line2) && (
            <Typography 
              variant="body1" 
              color="text.secondary" 
              sx={{ 
                mb: 3,
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              {(mentor as any).hero_subline}
            </Typography>
          )}
          
          {/* 4) Trust Layer */}
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2, mb: 2 }}>
            {(mentor as any).rating !== null && (mentor as any).rating !== undefined ? (
              <>
                <Rating value={(mentor as any).rating} readOnly />
                <Typography variant="body1">
                  ({(mentor as any).review_count || mentor.total_reviews})
                </Typography>
              </>
            ) : (
              (mentor as any).trust_label && (
                <Typography variant="body1" color="text.secondary">
                  {(mentor as any).trust_label}
                </Typography>
              )
            )}
          </Box>
          
          {/* 5) Price Anchor */}
          {(mentor as any).price_label && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {(mentor as any).price_label}
            </Typography>
          )}
          
          {/* 6) Primary CTA */}
          {(mentor as any).cta_label && (
            <Button
              variant="contained"
              size="large"
              onClick={() => {
                setTabValue(1);
              }}
              sx={{ 
                textTransform: 'none', 
                fontWeight: 600,
                '& .MuiButton-label': {
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  lineHeight: 1.1,
                  textAlign: 'center',
                },
              }}
            >
              {(mentor as any).cta_label}
            </Button>
          )}
        </Box>

        <Grid container spacing={3}>
          {/* ===== Profile Card ===== */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Avatar
                  src={mentor.user.avatar}
                  sx={{ width: 120, height: 120, mx: 'auto', mb: 2 }}
                />
                <Typography variant="h5">
                  {mentor.user.first_name} {mentor.user.last_name}
                </Typography>

                {mentor.is_verified && (
                  <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
                    <VerifiedIcon color="primary" fontSize="small" />
                    <Typography variant="body2" color="primary" sx={{ ml: 0.5 }}>
                      Verified Mentor
                    </Typography>
                  </Box>
                )}

                <Typography color="text.secondary" sx={{ mt: 1 }}>
                  {mentor.current_position}
                </Typography>

                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Rating value={mentor.average_rating} readOnly />
                  <Typography variant="body2" sx={{ ml: 1 }}>
                    ({mentor.total_reviews})
                  </Typography>
                </Box>

                <Button
                  sx={{ mt: 2 }}
                  fullWidth
                  variant="outlined"
                  onClick={() => setTabValue(1)}
                >
                  View Services
                </Button>
              </CardContent>
            </Card>
          </Grid>

          {/* ===== Main ===== */}
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
                  <Tab label="About" />
                  <Tab label="Services" />
                  <Tab label="Reviews" />
                </Tabs>

                <Box sx={{ mt: 3 }}>
                  {tabValue === 0 && (
                    <Box>
                      <Typography variant="body1" sx={{ mb: 2 }}>
                        {mentor.bio}
                      </Typography>
                      <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>
                        Experience
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {mentor.years_of_experience} years of experience
                      </Typography>
                      {specializations.length > 0 && (
                        <>
                          <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>
                            Specializations
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                            {specializations.map((spec, idx) => (
                              <Chip key={idx} label={spec} size="small" />
                            ))}
                          </Box>
                        </>
                      )}
                    </Box>
                  )}
                  {tabValue === 1 && (
                    <Box id="services-section">
                      <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                        How I can help you
                      </Typography>
                      {selectedServiceId && (
                        <Alert severity="info" sx={{ mb: 3 }}>
                          You are continuing with: <strong>{selectedService?.title}</strong>
                        </Alert>
                      )}
                      <Grid container spacing={2}>
                        {orderedServices.map(service => {
                          const isSelected = selectedServiceId === service.id;
                          return (
                            <Grid item xs={12} key={service.id}>
                              <Paper 
                                sx={{ 
                                  p: 2,
                                  border: isSelected ? 2 : 1,
                                  borderColor: isSelected ? 'primary.main' : 'divider',
                                  bgcolor: isSelected ? 'action.selected' : 'background.paper'
                                }}
                              >
                                <Typography variant="h6">{service.title}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {service.description}
                                </Typography>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                                  <Typography color="primary">{service.display_price}</Typography>
                                  <Button
                                    variant="contained"
                                    size="small"
                                    onClick={() => handleServiceContinue(service)}
                                  >
                                    Continue
                                  </Button>
                                </Box>
                              </Paper>
                            </Grid>
                          );
                        })}
                      </Grid>
                    </Box>
                  )}

                  {tabValue === 2 && (
                    <Box>
                      {((mentor as any).review_count || mentor.total_reviews) < 3 ? (
                        <Typography color="text.secondary">
                          {(mentor as any).trust_label || 'This mentor is newly reviewed and carefully verified by our platform.'}
                        </Typography>
                      ) : (
                        reviews.slice(0, 5).map(review => (
                          <Paper key={review.id} sx={{ p: 2, mb: 2 }}>
                            <Rating value={review.rating} readOnly size="small" />
                            <Typography>{review.comment}</Typography>
                            <Typography variant="caption">
                              {format(parseISO(review.created_at), 'MMM dd, yyyy')}
                            </Typography>
                          </Paper>
                        ))
                      )}
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>

      {/* ===== Booking Dialog ===== */}
      <Dialog open={bookingDialogOpen} onClose={() => setBookingDialogOpen(false)} fullWidth>
        <DialogTitle>Book Session</DialogTitle>
        <DialogContent>
          <TextField
            type="date"
            fullWidth
            sx={{ mt: 2 }}
            inputProps={{ min: format(addDays(new Date(), 1), 'yyyy-MM-dd') }}
            value={bookingForm.scheduled_date ? format(bookingForm.scheduled_date, 'yyyy-MM-dd') : ''}
            onChange={e => {
              const d = e.target.value ? new Date(e.target.value) : null;
              setBookingForm(prev => ({ ...prev, scheduled_date: d, scheduled_time: '' }));
              if (d) fetchAvailableSlots(d, bookingForm.service_id);
            }}
          />

          {bookingForm.scheduled_date && (
            <FormControl fullWidth sx={{ mt: 2 }}>
              <InputLabel>Time</InputLabel>
              <Select
                value={bookingForm.scheduled_time}
                onChange={e => setBookingForm(prev => ({ ...prev, scheduled_time: e.target.value }))}
                disabled={loadingSlots}
              >
                {availableSlots.map(slot => (
                  <MenuItem key={slot.start_time} value={slot.start_time}>
                    {slot.start_time} – {slot.end_time}
                  </MenuItem>
                ))}
              </Select>
              {loadingSlots && <FormHelperText>Loading slots…</FormHelperText>}
            </FormControl>
          )}

          <TextField
            fullWidth
            multiline
            rows={3}
            sx={{ mt: 2 }}
            label="Notes (optional)"
            value={bookingForm.user_notes}
            onChange={e => setBookingForm(prev => ({ ...prev, user_notes: e.target.value }))}
          />
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setBookingDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleBookingSubmit}
            disabled={!bookingForm.scheduled_time}
          >
            Confirm Booking
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default MentorDetailPage;
