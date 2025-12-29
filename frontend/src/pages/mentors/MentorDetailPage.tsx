import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Rating,
  Button,
  Paper,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { format, parseISO } from 'date-fns';

import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import { useNotification } from '../../components/common/NotificationProvider';
import mentorService from '../../services/api/mentorService';
import { sessionService } from '../../services/api/sessionService';
import MentorSidebarCard from '../../components/mentors/MentorSidebarCard';
import apiClient from '../../services/api/client';

import { MentorDetail, MentorService } from '../../types';
import { createApiError, handleApiError } from '../../services/utils/errorHandler';
import type { ApiError } from '../../services/utils/errorHandler';

/* =====================
   Helpers
===================== */

const parseWallTime = (iso: string): Date => {
  return new Date(iso);
};

/* =====================
   Types
===================== */

interface MentorReview {
  id: number;
  rating: number;
  comment: string;
  created_at: string;
  user: {
    username: string;
  };
}

interface Slot {
  id: number;
  start_time: string;
  end_time: string;
}

interface UISlot {
  parent_slot_id: number;
  start_time: string;
  end_time: string;
}

/* =====================
   Component
===================== */

const MentorDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { showError } = useNotification();

  const [mentor, setMentor] = useState<MentorDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const [tabValue, setTabValue] = useState(0);
  const [bookingDialogOpen, setBookingDialogOpen] = useState(false);
  const [weekOffset, setWeekOffset] = useState(0);

  const [availableSlots, setAvailableSlots] = useState<Slot[]>([]);
  const [uiSlots, setUiSlots] = useState<UISlot[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [slotsLoaded, setSlotsLoaded] = useState(false);
  const [disabledSlots, setDisabledSlots] = useState<Set<number>>(new Set());
  const [selectedServiceId, setSelectedServiceId] = useState<number | null>(null);

  /* =====================
     Data Fetch
  ===================== */

  const fetchMentorDetails = useCallback(async () => {
    try {
      setLoading(true);
      const data = await mentorService.getMentorById(Number(id));
      setMentor(data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) fetchMentorDetails();
  }, [id, fetchMentorDetails]);

  /* =====================
     Booking Helpers
  ===================== */

  const splitSlotsIntoHours = (slots: Slot[]): UISlot[] => {
    const result: UISlot[] = [];
    const now = new Date();

    slots.forEach((slot) => {
      let cursor = parseWallTime(slot.start_time);
      const end = parseWallTime(slot.end_time);

      // Last-resort guard: skip slots that are in the past
      if (cursor.getTime() <= now.getTime()) {
        return;
      }

      while (cursor.getTime() + 60 * 60 * 1000 <= end.getTime()) {
        const next = new Date(cursor.getTime() + 60 * 60 * 1000);

        // Filter out past UI slots (client-side safety check)
        if (cursor.getTime() > now.getTime()) {
          result.push({
            parent_slot_id: slot.id,
            start_time: cursor.toISOString(),
            end_time: next.toISOString(),
          });
        }

        cursor = next;
      }
    });

    return result;
  };

  const fetchAvailableSlots = useCallback(async () => {
    if (!mentor) return;
    try {
      setLoadingSlots(true);
      setSlotsLoaded(false);
      
      const today = new Date();
      const baseDate = new Date(today);
      baseDate.setDate(today.getDate() + weekOffset * 7);
      
      const dayOfWeek = baseDate.getDay();
      const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
      const monday = new Date(baseDate);
      monday.setDate(baseDate.getDate() + mondayOffset);
      monday.setHours(0, 0, 0, 0);
      
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);
      sunday.setHours(23, 59, 59, 999);
      
      const response = await apiClient.get('/appointments/time-slots/', {
        params: {
          mentor_id: mentor.id,
          from: format(monday, 'yyyy-MM-dd'),
          to: format(sunday, 'yyyy-MM-dd'),
        },
      });
      
      const slots = response.data || [];
      setAvailableSlots(slots);
      setUiSlots(splitSlotsIntoHours(slots));
      setSlotsLoaded(true);
    } catch {
      setAvailableSlots([]);
      setUiSlots([]);
      setSlotsLoaded(true);
    } finally {
      setLoadingSlots(false);
    }
  }, [mentor, weekOffset]);

  const openBooking = () => {
    setWeekOffset(0);
    setAvailableSlots([]);
    setUiSlots([]);
    setDisabledSlots(new Set());
    setSlotsLoaded(false);
    if (!selectedServiceId && mentor?.primary_service_id) {
      setSelectedServiceId(mentor.primary_service_id);
    }
    setBookingDialogOpen(true);
  };

  const handleServiceContinue = (service: MentorService) => {
    setSelectedServiceId(service.id);
    openBooking();
  };

  useEffect(() => {
    if (bookingDialogOpen) {
      fetchAvailableSlots();
    }
  }, [bookingDialogOpen, weekOffset, fetchAvailableSlots]);

  const handleWeekChange = (offset: number) => {
    setWeekOffset(offset);
  };

  const handleSlotClick = async (uiSlot: UISlot) => {
    if (!uiSlot.parent_slot_id || disabledSlots.has(uiSlot.parent_slot_id)) return;

    if (!selectedServiceId) {
      showError('Please select a service first');
      return;
    }

    const selectedService = mentor?.services?.find(
      (service) => service.id === selectedServiceId
    );
    const sessionTitle = selectedService?.title
      ? selectedService.title
      : `Session with ${mentor?.display_name || mentor?.user?.username || 'mentor'}`;

    // ========== STEP 1: Lock Slot ==========
    let appointmentId: number;
  
    try {
      const lockResponse = await sessionService.lockSlot({
        time_slot_id: uiSlot.parent_slot_id,
        service_id: selectedServiceId,
        title: sessionTitle,
        description: '',
      });
  
      appointmentId = lockResponse.data.appointment.id;
    } catch (error: any) {
      if (error.response?.status === 409) {
        setDisabledSlots(prev => new Set(prev).add(uiSlot.parent_slot_id));
        showError('This time was just taken. Please pick another slot.');
      } else {
        showError('Failed to lock time slot. Please try again.');
      }
      return; // ❗非常重要：锁失败就直接结束
    }
  
    // ========== STEP 2: Create Checkout Session ==========
    try {
      const checkoutResponse = await apiClient.post(
        '/payments/create-checkout-session/',
        { appointment_id: appointmentId }
      );
  
      window.location.href = checkoutResponse.data.checkout_url;
    } catch (error: any) {
      // Show distinct error message for payment step failures
      showError('Slot locked, but failed to start payment. Please try again.');
    }
  };

  const services = mentor?.services ?? [];
  const reviews: MentorReview[] = mentor?.reviews ?? [];
  const activeServices = services.filter(s => s.is_active !== false);
  const primaryService =
    mentor?.primary_service_id &&
    activeServices.find(s => s.id === mentor.primary_service_id);
  const orderedServices = primaryService
    ? [primaryService, ...activeServices.filter(s => s.id !== primaryService.id)]
    : activeServices;
  const pageTitle =
    mentor?.display_name ??
    (
      `${mentor?.user?.first_name ?? ''} ${mentor?.user?.last_name ?? ''}`.trim() || 'Mentor'
    );

  const selectedService = useMemo(() => {
    if (selectedServiceId) {
      return services.find(service => service.id === selectedServiceId);
    }
    return primaryService ?? orderedServices[0];
  }, [orderedServices, primaryService, selectedServiceId, services]);

  const timezoneLabel = useMemo(() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch {
      return 'your local time';
    }
  }, []);

  const slotGroups = useMemo(() => {
    return uiSlots.reduce<Record<string, UISlot[]>>((acc, uiSlot) => {
      const start = parseWallTime(uiSlot.start_time);
      const dateStr = format(start, 'EEEE, MMM dd');
      if (!acc[dateStr]) acc[dateStr] = [];
      acc[dateStr].push(uiSlot);
      return acc;
    }, {});
  }, [uiSlots]);

  const bioText = mentor?.bio
    ? mentor.bio.replace(/^###\s*/gm, '')
    : 'No bio available yet.';

  /* =====================
     Guards
  ===================== */

  if (loading) return <LoadingSpinner />;
  if (error || !mentor) {
    return (
      <ErrorAlert
        error={error || createApiError('Mentor not found', 'NOT_FOUND_ERROR')}
      />
    );
  }

  if (activeServices.length === 0) {
    return (
      <ErrorAlert
        error={createApiError('This mentor has no active services available.', 'NOT_FOUND_ERROR')}
      />
    );
  }
  /* =====================
     Render
  ===================== */

  return (
    <>
      <PageHeader
      title={pageTitle}
      breadcrumbs={[
        { label: 'Mentors', path: '/student/mentors' },
        { label: pageTitle, path: `/student/mentors/${mentor.id}` },
      ]}
      />

      <Container maxWidth="lg">
        {/* ===== Hero Section ===== */}
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          {mentor.hero_title && (
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mb: 1, textTransform: 'uppercase', letterSpacing: '0.5px' }}
            >
              {mentor.hero_title}
            </Typography>
          )}

          <Typography variant="h4" sx={{ fontWeight: 700, mb: 2 }}>
            {mentor.hero_headline ?? mentor.mentor_card?.line1}
          </Typography>

          {mentor.hero_subline && (
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              {mentor.hero_subline}
            </Typography>
          )}

          {mentor.price_label && (
            <Typography color="text.secondary" sx={{ mb: 3 }}>
              {mentor.price_label}
            </Typography>
          )}

          {mentor.cta_label && (
            <Button
              variant="contained"
              size="large"
              onClick={openBooking}
              sx={{ textTransform: 'none', fontWeight: 600 }}
            >
              {mentor.cta_label}
            </Button>
          )}
        </Box>

        <Grid container spacing={3}>
          {/* ===== Sidebar ===== */}
          <Grid item xs={12} md={4}>
            <MentorSidebarCard
              mentor={mentor}
              onViewServices={() => setTabValue(1)}
            />
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
                    <Typography sx={{ whiteSpace: 'pre-line' }}>
                      {bioText}
                    </Typography>
                  )}

                  {tabValue === 1 && (
                    <Grid container spacing={2}>
                      {orderedServices.map(service => (
                        <Grid item xs={12} key={service.id}>
                          <Paper sx={{ p: 2 }}>
                            <Typography fontWeight={600}>
                              {service.title}
                            </Typography>
                            <Typography color="text.secondary">
                              {service.description}
                            </Typography>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                              <Typography color="primary">
                                {service.display_price}
                              </Typography>
                              <Button
                                variant="contained"
                                size="small"
                                onClick={() => handleServiceContinue(service)}
                              >
                                Book this session
                              </Button>
                            </Box>
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  )}

                  {tabValue === 2 && (
                    <Box>
                      {mentor.trust_label && (
                        <Typography color="text.secondary" sx={{ mb: 2 }}>
                          {mentor.trust_label}
                        </Typography>
                      )}
                      {reviews.length === 0 ? (
                        <Typography color="text.secondary">No reviews yet.</Typography>
                      ) : (
                        reviews.map((review: MentorReview) => (
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
        <Dialog open={bookingDialogOpen} onClose={() => setBookingDialogOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>Book Session</DialogTitle>
        <DialogContent>
          {selectedService && (
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography fontWeight={700}>{selectedService.title}</Typography>
              {selectedService.description && (
                <Typography color="text.secondary">{selectedService.description}</Typography>
              )}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                <Typography color="primary">{selectedService.display_price}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Times shown in {timezoneLabel}
                </Typography>
              </Box>
            </Paper>
          )}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Button
              variant={weekOffset === 0 ? 'contained' : 'outlined'}
              size="small"
              onClick={() => handleWeekChange(0)}
              disabled={weekOffset === 0}
            >
              This Week
            </Button>
            <Button
              variant="outlined"
              size="small"
              onClick={() => handleWeekChange(weekOffset + 1)}
            >
              Next Week
            </Button>
          </Box>

          {loadingSlots || !slotsLoaded ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography>Loading available slots...</Typography>
            </Box>
          ) : slotsLoaded && uiSlots.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography color="text.secondary">No available slots this week</Typography>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxHeight: 400, overflow: 'auto' }}>
              {Object.entries(slotGroups).map(([dateLabel, slots]) => (
                <Box key={dateLabel}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    {dateLabel}
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {slots.map((uiSlot) => {
                      const start = parseWallTime(uiSlot.start_time);
                      const end = parseWallTime(uiSlot.end_time);

                      const startTimeStr = format(start, 'HH:mm');
                      const endTimeStr = format(end, 'HH:mm');

                      return (
                        <Button
                          key={`${uiSlot.parent_slot_id}-${uiSlot.start_time}`}
                          variant="outlined"
                          fullWidth
                          onClick={() => handleSlotClick(uiSlot)}
                          disabled={disabledSlots.has(uiSlot.parent_slot_id)}
                          sx={{
                            justifyContent: 'flex-start',
                            textTransform: 'none',
                            py: 1.5,
                          }}
                        >
                          <Typography>
                            {startTimeStr} – {endTimeStr}
                          </Typography>
                        </Button>
                      );
                    })}
                  </Box>
                </Box>
              ))}
            </Box>
          )}
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setBookingDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default MentorDetailPage;
