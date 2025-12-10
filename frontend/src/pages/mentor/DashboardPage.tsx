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
} from '@mui/icons-material';
import { RootState } from '../../store';
import LoadingSpinner from '../../components/common/LoadingSpinner';

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
  const [stats, setStats] = useState({
    upcomingToday: 2,
    upcomingThisWeek: 5,
    pendingRequests: 3,
    monthlyEarnings: 1250,
    averageRating: 4.8,
  });
  const [upcomingAppointments, setUpcomingAppointments] = useState<UpcomingAppointment[]>([]);

  useEffect(() => {
    setTimeout(() => {
      setUpcomingAppointments([
        {
          id: 1,
          student: { name: 'Alice Johnson' },
          session_type: 'Career Chat',
          scheduled_at: '2025-01-20T14:00:00Z',
          duration: 60,
        },
        {
          id: 2,
          student: { name: 'Bob Smith' },
          session_type: 'Resume Review',
          scheduled_at: '2025-01-20T16:00:00Z',
          duration: 45,
        },
        {
          id: 3,
          student: { name: 'Charlie Brown' },
          session_type: 'Mock Interview',
          scheduled_at: '2025-01-21T10:00:00Z',
          duration: 60,
        },
      ]);
      setLoading(false);
    }, 500);
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading dashboard..." />;
  }

  const mentorName = user?.first_name || user?.username || 'Mentor';

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
                  Pending Requests
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {stats.pendingRequests}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Awaiting approval
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
                ${stats.monthlyEarnings}
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
                From 45 reviews
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

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

