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
import appointmentService from '../../services/api/appointmentService';

interface MentorDetail {
  id: number;
  user: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    avatar?: string;
  };
  bio: string;
  years_of_experience: number;
  current_position: string;
  industry: string;
  status: string;
  average_rating: number;
  total_reviews: number;
  total_sessions: number;
  total_earnings: number;
  is_verified: boolean;
  verification_badge: string;
  specializations: string[];
  ranking_score: number;
  is_approved: boolean;
  created_at: string;
  updated_at: string;
  services: MentorService[];
  reviews: MentorReview[];
  availability: MentorAvailability[];
}

interface MentorService {
  id: number;
  service_type: string;
  title: string;
  description: string;
  pricing_model: string;
  price_per_hour?: number;
  fixed_price?: number;
  package_price?: number;
  package_sessions?: number;
  duration_minutes: number;
  display_price: string;
  is_active: boolean;
}

interface MentorReview {
  id: number;
  rating: number;
  comment: string;
  created_at: string;
  user: {
    username: string;
    avatar?: string;
  };
}

interface MentorAvailability {
  id: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  is_active: boolean;
}

interface BookingForm {
  service_id: number;
  scheduled_date: Date | null;
  scheduled_time: string;
  user_notes: string;
  duration_minutes?: number;
}

interface MentorDetailPageProps {
  initialTab?: 'booking';
}

const MentorDetailPage: React.FC<MentorDetailPageProps> = ({ initialTab }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();
  
  const [mentor, setMentor] = useState<MentorDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [bookingDialogOpen, setBookingDialogOpen] = useState(false);
  const [availableSlots, setAvailableSlots] = useState<Array<{
    start_time: string;
    end_time: string;
    duration_minutes: number;
  }>>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  
  const [bookingForm, setBookingForm] = useState<BookingForm>({
    service_id: 0,
    scheduled_date: null,
    scheduled_time: '',
    user_notes: '',
  });

  const fetchMentorDetails = useCallback(async () => {
    try {
      setLoading(true);
      const mentorData = await mentorService.getMentorById(parseInt(id!));
      setMentor(mentorData);
      console.log('Mentor data loaded:', mentorData);
      console.log('Services count:', mentorData.services?.length || 0);
      console.log('Availability count:', mentorData.availability?.length || 0);
    } catch (err) {
      setError('Failed to load mentor details');
      console.error('Mentor details error:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      fetchMentorDetails();
    }
  }, [id, fetchMentorDetails]);

  // Auto-open booking dialog if initialTab is 'booking'
  useEffect(() => {
    if (initialTab === 'booking' && mentor && !loading) {
      setBookingDialogOpen(true);
    }
  }, [initialTab, mentor, loading]);

  const fetchAvailableSlots = async (date: Date, serviceId?: number) => {
    if (!mentor) return;
    
    try {
      setLoadingSlots(true);
      const formattedDate = format(date, 'yyyy-MM-dd');
      console.log('Fetching slots for date:', formattedDate, 'mentor ID:', mentor.id, 'service ID:', serviceId);
      
      const params: any = { date: formattedDate };
      if (serviceId) {
        params.service_id = serviceId;
      }
      
      const slots = await mentorService.getMentorAvailability(mentor.id, formattedDate, serviceId);
      console.log('Received slots:', slots);
      setAvailableSlots(slots.map((slot: any) => ({
        start_time: slot.start_time,
        end_time: slot.end_time,
        duration_minutes: slot.duration_minutes
      })));
      console.log('Processed slots:', slots.map((slot: any) => slot.start_time));
    } catch (err) {
      console.error('Failed to fetch available slots:', err);
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleDateChange = (date: Date | null) => {
    setBookingForm(prev => ({ ...prev, scheduled_date: date, scheduled_time: '' }));
    if (date) {
      fetchAvailableSlots(date, bookingForm.service_id);
    }
  };

  const handleServiceChange = (serviceId: number) => {
    setBookingForm(prev => ({ ...prev, service_id: serviceId, scheduled_time: '' }));
    if (bookingForm.scheduled_date) {
      fetchAvailableSlots(bookingForm.scheduled_date, serviceId);
    }
  };

  const handleBookingSubmit = async () => {
    if (!mentor || !bookingForm.scheduled_date) return;

    try {
      const appointmentData = {
        mentor_id: mentor.id,
        service_id: bookingForm.service_id,
        scheduled_date: format(bookingForm.scheduled_date, 'yyyy-MM-dd'),
        scheduled_time: bookingForm.scheduled_time,
        user_notes: bookingForm.user_notes,
      };

      await appointmentService.createAppointment(appointmentData);
      showSuccess('Appointment booked successfully!');
      setBookingDialogOpen(false);
      // Navigate to appointments list after successful booking
      navigate('/appointments');
    } catch (err) {
      showError('Failed to book appointment');
      console.error('Booking error:', err);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error || !mentor) {
    return <ErrorAlert message={error || 'Mentor not found'} />;
  }

  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  return (
    <>
      <PageHeader
        title={`${mentor.user.first_name} ${mentor.user.last_name}`}
        breadcrumbs={[
          { label: 'Mentors', path: '/mentors' },
          { label: mentor.user.first_name, path: `/mentors/${mentor.id}` }
        ]}
      />

      <Container maxWidth="lg">
        <Grid container spacing={3}>
          {/* Mentor Profile Card */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Avatar
                  src={mentor.user.avatar}
                  sx={{ width: 120, height: 120, mx: 'auto', mb: 2 }}
                >
                  {mentor.user.first_name[0]}{mentor.user.last_name[0]}
                </Avatar>
                
                <Typography variant="h5" gutterBottom>
                  {mentor.user.first_name} {mentor.user.last_name}
                </Typography>
                
                {mentor.is_verified && (
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                    <VerifiedIcon color="primary" fontSize="small" />
                    <Typography variant="body2" color="primary" sx={{ ml: 0.5 }}>
                      Verified Mentor
                    </Typography>
                  </Box>
                )}
                
                <Typography variant="body1" color="text.secondary" gutterBottom>
                  {mentor.current_position}
                </Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
                  <Rating value={mentor.average_rating} readOnly precision={0.5} />
                  <Typography variant="body2" sx={{ ml: 1 }}>
                    ({mentor.total_reviews} reviews)
                  </Typography>
                </Box>
                
                <Button
                  variant="contained"
                  fullWidth
                  onClick={() => navigate(`/mentors/${mentor.id}/book`)}
                  disabled={mentor.services.length === 0}
                >
                  Book Session
                </Button>
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Quick Stats
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <WorkIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary={`${mentor.years_of_experience} years experience`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <EventIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary={`${mentor.total_sessions} sessions completed`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <MoneyIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary={`$${mentor.total_earnings} total earnings`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <BusinessIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary={mentor.industry}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Main Content */}
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Tabs value={tabValue} onChange={handleTabChange}>
                  <Tab label="About" />
                  <Tab label="Services" />
                  <Tab label="Availability" />
                  <Tab label="Reviews" />
                </Tabs>

                <Box sx={{ mt: 3 }}>
                  {/* About Tab */}
                  {tabValue === 0 && (
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        About {mentor.user.first_name}
                      </Typography>
                      <Typography variant="body1" paragraph>
                        {mentor.bio}
                      </Typography>
                      
                      <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                        Specializations
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {mentor.specializations.map((spec, index) => (
                          <Chip key={index} label={spec} variant="outlined" />
                        ))}
                      </Box>
                    </Box>
                  )}

                  {/* Services Tab */}
                  {tabValue === 1 && (
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Services Offered
                      </Typography>
                      {mentor.services.length === 0 ? (
                        <Alert severity="info">No services available at the moment.</Alert>
                      ) : (
                        <Grid container spacing={2}>
                          {mentor.services.map((service) => (
                            <Grid item xs={12} key={service.id}>
                              <Paper sx={{ p: 2 }}>
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
                                    <Button
                                      variant="outlined"
                                      size="small"
                                      onClick={() => {
                                        setBookingForm(prev => ({ ...prev, service_id: service.id }));
                                        setBookingDialogOpen(true);
                                      }}
                                    >
                                      Book Now
                                    </Button>
                                  </Box>
                                </Box>
                              </Paper>
                            </Grid>
                          ))}
                        </Grid>
                      )}
                    </Box>
                  )}

                  {/* Availability Tab */}
                  {tabValue === 2 && (
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Weekly Availability
                      </Typography>
                      {mentor.availability.length === 0 ? (
                        <Alert severity="info">No availability information available.</Alert>
                      ) : (
                        <Grid container spacing={2}>
                          {mentor.availability.map((slot) => (
                            <Grid item xs={12} sm={6} key={slot.id}>
                              <Paper sx={{ p: 2 }}>
                                <Typography variant="subtitle1" fontWeight="bold">
                                  {dayNames[slot.day_of_week]}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {slot.start_time} - {slot.end_time}
                                </Typography>
                              </Paper>
                            </Grid>
                          ))}
                        </Grid>
                      )}
                    </Box>
                  )}

                  {/* Reviews Tab */}
                  {tabValue === 3 && (
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Reviews ({mentor.total_reviews})
                      </Typography>
                      {mentor.reviews.length === 0 ? (
                        <Alert severity="info">No reviews yet.</Alert>
                      ) : (
                        <Box>
                          {mentor.reviews.map((review) => (
                            <Paper key={review.id} sx={{ p: 2, mb: 2 }}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                  <Avatar sx={{ width: 32, height: 32, mr: 1 }}>
                                    {review.user.username[0]}
                                  </Avatar>
                                  <Typography variant="subtitle2">
                                    {review.user.username}
                                  </Typography>
                                </Box>
                                <Rating value={review.rating} readOnly size="small" />
                              </Box>
                              <Typography variant="body2" color="text.secondary">
                                {review.comment}
                              </Typography>
                              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                {format(parseISO(review.created_at), 'MMM dd, yyyy')}
                              </Typography>
                            </Paper>
                          ))}
                        </Box>
                      )}
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>

      {/* Booking Dialog */}
      <Dialog 
        open={bookingDialogOpen} 
        onClose={() => setBookingDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Book Session with {mentor.user.first_name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Select Service</InputLabel>
              <Select
                value={bookingForm.service_id}
                onChange={(e) => handleServiceChange(e.target.value as number)}
                label="Select Service"
              >
                {mentor.services.map((service) => (
                  <MenuItem key={service.id} value={service.id}>
                    {service.title} - {service.display_price}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              type="date"
              label="Select Date"
              value={bookingForm.scheduled_date ? format(bookingForm.scheduled_date, 'yyyy-MM-dd') : ''}
              onChange={(e) => {
                const date = e.target.value ? new Date(e.target.value) : null;
                handleDateChange(date);
              }}
              inputProps={{
                min: format(addDays(new Date(), 1), 'yyyy-MM-dd')
              }}
              fullWidth
              sx={{ mb: 2 }}
            />

            {bookingForm.scheduled_date && (
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Select Time</InputLabel>
                <Select
                  value={bookingForm.scheduled_time}
                  onChange={(e) => setBookingForm(prev => ({ ...prev, scheduled_time: e.target.value }))}
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
                      <MenuItem key={slot.start_time} value={slot.start_time}>
                        {slot.start_time} - {slot.end_time} ({slot.duration_minutes} min)
                      </MenuItem>
                    ))
                  )}
                </Select>
                {loadingSlots && <FormHelperText>Loading available time slots...</FormHelperText>}
                                    {!loadingSlots && availableSlots.length > 0 && (
                      <FormHelperText>{availableSlots.length} slots available</FormHelperText>
                    )}
              </FormControl>
            )}

            <TextField
              fullWidth
              multiline
              rows={3}
              label="Notes (Optional)"
              value={bookingForm.user_notes}
              onChange={(e) => setBookingForm(prev => ({ ...prev, user_notes: e.target.value }))}
              placeholder="Any specific topics or questions you'd like to discuss..."
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBookingDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleBookingSubmit}
            variant="contained"
            disabled={!bookingForm.service_id || !bookingForm.scheduled_date || !bookingForm.scheduled_time}
          >
            Book Session
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default MentorDetailPage; 