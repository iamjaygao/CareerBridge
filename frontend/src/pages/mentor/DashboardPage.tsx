import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Avatar,
  Alert,
} from '@mui/material';
import {
  Event as EventIcon,
  Schedule as ScheduleIcon,
  AttachMoney as MoneyIcon,
  Star as StarIcon,
  CheckCircle as CheckCircleIcon,
  ArrowForward as ArrowForwardIcon,
  NotificationsActive as NotificationsActiveIcon,
} from '@mui/icons-material';
import { RootState } from '../../store';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import appointmentService from '../../services/api/appointmentService';
import mentorService from '../../services/api/mentorService';
import { getNotifications, Notification } from '../../services/api/notificationService';

interface UpcomingAppointment {
  id: number;
  student: {
    name: string;
    avatar?: string;
  };
  session_type: string;
  scheduled_at: string;
  duration: number;
}

const MentorDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({
    upcomingToday: 0,
    upcomingThisWeek: 0,
    nextTwoWeeks: 0,
    monthlyEarnings: 0,
    averageRating: 0,
    reviewCount: 0,
  });
  const [upcomingAppointments, setUpcomingAppointments] = useState<UpcomingAppointment[]>([]);
  const [reminders, setReminders] = useState<Notification[]>([]);
  const [actionItems, setActionItems] = useState({
    pendingConfirmations: 0,
    upcoming24h: 0,
    missingFeedback: 0,
  });

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setError(null);
        const [statsResult, appointmentsResult, profileResult, notificationsResult] = await Promise.allSettled([
          appointmentService.getAppointmentStats(),
          appointmentService.getMentorAppointments(),
          mentorService.getMyProfile(),
          getNotifications({ is_read: false, limit: 6 }),
        ]);

        const appointments = appointmentsResult.status === 'fulfilled'
          ? (Array.isArray(appointmentsResult.value)
              ? appointmentsResult.value
              : ((appointmentsResult.value as any)?.results || []))
          : [];

        const now = new Date();
        const weekAhead = new Date();
        weekAhead.setDate(now.getDate() + 7);

        const upcoming = appointments.filter((apt: any) => {
          if (!apt.scheduled_start) return false;
          const start = new Date(apt.scheduled_start);
          return (apt.status === 'pending' || apt.status === 'confirmed') && start > now;
        });

        const upcomingThisWeek = upcoming.filter((apt: any) => new Date(apt.scheduled_start) <= weekAhead).length;
        const twoWeeksAhead = new Date(now);
        twoWeeksAhead.setDate(now.getDate() + 14);
        const nextTwoWeeks = upcoming.filter((apt: any) => new Date(apt.scheduled_start) <= twoWeeksAhead).length;
        const upcomingToday = appointments.filter((apt: any) => {
          if (!apt.scheduled_start) return false;
          const start = new Date(apt.scheduled_start);
          return (apt.status === 'pending' || apt.status === 'confirmed') &&
            start.toDateString() === now.toDateString();
        }).length;

        const monthlyEarnings = appointments.reduce((total: number, apt: any) => {
          if (!apt.scheduled_start || !apt.price) return total;
          const start = new Date(apt.scheduled_start);
          const sameMonth = start.getMonth() === now.getMonth() && start.getFullYear() === now.getFullYear();
          if (!sameMonth) return total;
          if (apt.status !== 'confirmed' && apt.status !== 'completed') return total;
          const amount = typeof apt.price === 'string' ? parseFloat(apt.price) : Number(apt.price);
          return total + (Number.isNaN(amount) ? 0 : amount);
        }, 0);

        const averageRating = profileResult.status === 'fulfilled'
          ? (profileResult.value?.rating ?? profileResult.value?.average_rating ?? 0)
          : 0;
        const reviewCount = profileResult.status === 'fulfilled'
          ? (profileResult.value?.review_count ?? profileResult.value?.total_reviews ?? 0)
          : 0;

        const notificationList = notificationsResult.status === 'fulfilled'
          ? (notificationsResult.value?.results || [])
          : [];
        const reminderItems = notificationList
          .filter((notice) => !notice.is_read)
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
          .slice(0, 3);

        const upcomingCards = upcoming
          .sort((a: any, b: any) => new Date(a.scheduled_start).getTime() - new Date(b.scheduled_start).getTime())
          .slice(0, 3)
          .map((apt: any) => {
            const studentName = apt.user
              ? `${apt.user.first_name || ''} ${apt.user.last_name || ''}`.trim() || apt.user.username
              : 'Student';
            const duration = apt.scheduled_start && apt.scheduled_end
              ? Math.round((new Date(apt.scheduled_end).getTime() - new Date(apt.scheduled_start).getTime()) / (1000 * 60))
              : 60;
            return {
              id: apt.id,
              student: { name: studentName },
              session_type: apt.service?.title || apt.title || 'Session',
              scheduled_at: apt.scheduled_start,
              duration,
            };
          });

        const pendingConfirmations = appointments.filter((apt: any) => apt.status === 'pending').length;
        const missingFeedback = appointments.filter(
          (apt: any) => apt.status === 'completed' && !apt.mentor_feedback
        ).length;
        const upcoming24h = appointments.filter((apt: any) => {
          if (!apt.scheduled_start || apt.status !== 'confirmed') return false;
          const start = new Date(apt.scheduled_start);
          return start >= now && start <= new Date(now.getTime() + 24 * 60 * 60 * 1000);
        }).length;

        setStats({
          upcomingToday,
          upcomingThisWeek,
          nextTwoWeeks,
          monthlyEarnings: Number(monthlyEarnings.toFixed(2)),
          averageRating,
          reviewCount,
        });
        setUpcomingAppointments(upcomingCards);
        setReminders(reminderItems);
        setActionItems({
          pendingConfirmations,
          upcoming24h,
          missingFeedback,
        });
      } catch {
        setError('Failed to load mentor dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading dashboard..." />;
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  const mentorName = user?.first_name || user?.username || 'Mentor';
  const getPriorityColor = (priority?: Notification['priority']) => {
    switch (priority) {
      case 'urgent':
      case 'critical':
        return 'error.main';
      case 'high':
        return 'warning.main';
      case 'medium':
        return 'info.main';
      case 'low':
        return 'text.secondary';
      default:
        return 'primary.main';
    }
  };

  return (
    <Box>
      {/* Welcome Message */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Welcome back, {mentorName}!
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Here's what's happening with your mentoring sessions
        </Typography>
      </Box>

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <EventIcon sx={{ color: 'primary.main', mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Upcoming Today
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {stats.upcomingToday}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {stats.upcomingThisWeek} this week
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ScheduleIcon sx={{ color: 'warning.main', mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Next 2 Weeks
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {stats.nextTwoWeeks}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Upcoming sessions scheduled
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <MoneyIcon sx={{ color: 'success.main', mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  This Month's Earnings
                </Typography>
              </Box>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                ${stats.monthlyEarnings.toFixed(2)}
                </Typography>
              <Typography variant="caption" color="text.secondary">
                From {stats.upcomingThisWeek} sessions
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <StarIcon sx={{ color: 'warning.main', mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Average Rating
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {stats.averageRating}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                From {stats.reviewCount} reviews
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {reminders.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Reminders
            </Typography>
            <Button size="small" onClick={() => navigate('/mentor/notifications')}>
              View All
            </Button>
          </Box>
          <Grid container spacing={3}>
            {reminders.map((reminder) => (
              <Grid item xs={12} md={4} key={reminder.id}>
                <Card
                  onClick={() => navigate('/mentor/notifications')}
                  sx={{
                    height: '100%',
                    cursor: 'pointer',
                    borderLeft: '4px solid',
                    borderColor: getPriorityColor(reminder.priority),
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <NotificationsActiveIcon sx={{ color: getPriorityColor(reminder.priority), mr: 1 }} />
                      <Typography variant="body2" color="text.secondary">
                        {new Date(reminder.created_at).toLocaleString()}
                      </Typography>
                    </Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                      {reminder.title}
                    </Typography>
                    {reminder.message && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {reminder.message}
                      </Typography>
                    )}
                    {reminder.priority && (
                      <Chip
                        label={reminder.priority.toUpperCase()}
                        size="small"
                        sx={{ textTransform: 'uppercase' }}
                        color={reminder.priority === 'urgent' || reminder.priority === 'critical' ? 'error' : 'default'}
                      />
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      <Grid container spacing={3}>
        {/* Next Actions */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Next Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => navigate('/mentor/profile')}
                  sx={{ justifyContent: 'flex-start' }}
                >
                  Complete Your Profile
                </Button>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => navigate('/mentor/availability')}
                  sx={{ justifyContent: 'flex-start' }}
                >
                  Set Your Availability
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Upcoming Appointments */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Upcoming Appointments
                </Typography>
                <Button
                  size="small"
                  endIcon={<ArrowForwardIcon />}
                  onClick={() => navigate('/mentor/appointments')}
                >
                  View All
                </Button>
              </Box>
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Student</TableCell>
                      <TableCell>Session Type</TableCell>
                      <TableCell>Time</TableCell>
                      <TableCell>Duration</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {upcomingAppointments.map((appointment) => (
                      <TableRow key={appointment.id} hover>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Avatar sx={{ mr: 2, width: 32, height: 32 }}>
                              {appointment.student.name.charAt(0)}
                            </Avatar>
                            <Typography variant="body2" fontWeight="medium">
                              {appointment.student.name}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip label={appointment.session_type} size="small" />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {new Date(appointment.scheduled_at).toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {appointment.duration} min
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Action Items */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Action Items
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        Pending confirmations
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Approve or decline new requests
                      </Typography>
                    </Box>
                    <Chip label={actionItems.pendingConfirmations} color="warning" size="small" />
                  </Box>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => navigate('/mentor/appointments?tab=requests&status=pending')}
                  >
                    Review requests
                  </Button>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        Upcoming in 24h
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Confirm meeting links and prep
                      </Typography>
                    </Box>
                    <Chip label={actionItems.upcoming24h} color="success" size="small" />
                  </Box>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => navigate('/mentor/appointments?tab=upcoming&status=confirmed&window=24h')}
                  >
                    View schedule
                  </Button>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        Missing feedback
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Completed sessions without notes
                      </Typography>
                    </Box>
                    <Chip label={actionItems.missingFeedback} color="error" size="small" />
                  </Box>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => navigate('/mentor/appointments?tab=past&filter=missing_feedback')}
                  >
                    Add feedback
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Platform Announcements */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Platform Announcements
              </Typography>
              <Alert severity="info" sx={{ mb: 1 }}>
                <Typography variant="body2">
                  <strong>New Feature:</strong> Enhanced feedback system now available. Share detailed session notes with your students.
                </Typography>
              </Alert>
              <Alert severity="success">
                <Typography variant="body2">
                  <strong>Reminder:</strong> Update your availability for next week to maximize your booking potential.
                </Typography>
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MentorDashboardPage;
