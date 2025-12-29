import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Avatar,
  TextField,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as DeclineIcon,
  Edit as RescheduleIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import appointmentService from '../../services/api/appointmentService';
import { useNotification } from '../../components/common/NotificationProvider';

interface AppointmentRow {
  id: number;
  student: {
    name: string;
    email: string;
    avatar?: string;
  };
  session_type: string;
  scheduled_at: string;
  duration: number;
  status: string;
  isRequest?: boolean;
  mentor_feedback?: string;
}

const MentorAppointmentsPage: React.FC = () => {
  const { showSuccess, showError } = useNotification();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [appointments, setAppointments] = useState<AppointmentRow[]>([]);
  const [requests, setRequests] = useState<AppointmentRow[]>([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [windowFilter, setWindowFilter] = useState<'24h' | null>(null);
  const [missingFeedbackOnly, setMissingFeedbackOnly] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState<AppointmentRow | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'view' | 'approve' | 'decline' | 'reschedule'>('view');
  const [newDate, setNewDate] = useState('');
  const [newTime, setNewTime] = useState('');
  const location = useLocation();

  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        setError(null);
        const [appointmentsResult, requestsResult] = await Promise.allSettled([
          appointmentService.getMentorAppointments(),
          appointmentService.getAppointmentRequests(),
        ]);

        if (appointmentsResult.status === 'fulfilled') {
          const payload = appointmentsResult.value as any;
          const list = Array.isArray(payload) ? payload : (payload?.results || []);
          const rows = list.map((apt: any) => {
            const studentName = apt.user
              ? `${apt.user.first_name || ''} ${apt.user.last_name || ''}`.trim() || apt.user.username
              : 'Student';
            const duration = apt.scheduled_start && apt.scheduled_end
              ? Math.round((new Date(apt.scheduled_end).getTime() - new Date(apt.scheduled_start).getTime()) / (1000 * 60))
              : 60;
              return {
              id: apt.id,
              student: {
                name: studentName,
                email: apt.user?.email || '',
                avatar: apt.user?.avatar,
              },
              session_type: apt.service?.title || apt.title || 'Session',
              scheduled_at: apt.scheduled_start,
              duration,
              status: apt.status,
              mentor_feedback: apt.mentor_feedback || '',
            } as AppointmentRow;
          });
          setAppointments(rows);
        }

        if (requestsResult.status === 'fulfilled') {
          const payload = requestsResult.value as any;
          const list = Array.isArray(payload) ? payload : (payload?.results || []);
          const requestRows = list.map((req: any) => {
            const studentName = req.user
              ? `${req.user.first_name || ''} ${req.user.last_name || ''}`.trim() || req.user.username
              : 'Student';
            const scheduledAt = req.preferred_date && req.preferred_time_start
              ? `${req.preferred_date}T${req.preferred_time_start}`
              : '';
            const duration = req.preferred_time_start && req.preferred_time_end
              ? Math.round((new Date(`${req.preferred_date}T${req.preferred_time_end}`).getTime() - new Date(scheduledAt).getTime()) / (1000 * 60))
              : 60;
            return {
              id: req.id,
              student: {
                name: studentName,
                email: req.user?.email || '',
                avatar: req.user?.avatar,
              },
              session_type: req.title || 'Appointment Request',
              scheduled_at: scheduledAt,
              duration,
              status: req.status,
              isRequest: true,
            } as AppointmentRow;
          });
          setRequests(requestRows);
        }
      } catch {
        setError('Failed to load appointments.');
      } finally {
        setLoading(false);
      }
    };

    fetchAppointments();
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tabParam = params.get('tab');
    const statusParam = params.get('status');
    const filterParam = params.get('filter');
    const windowParam = params.get('window');

    if (tabParam === 'past') {
      setTabValue(1);
    } else if (tabParam === 'requests') {
      setTabValue(2);
    } else if (tabParam === 'upcoming') {
      setTabValue(0);
    }

    if (statusParam) {
      setStatusFilter(statusParam);
    } else {
      setStatusFilter('all');
    }

    setWindowFilter(windowParam === '24h' ? '24h' : null);
    setMissingFeedbackOnly(filterParam === 'missing_feedback');
  }, [location.search]);

  const handleAction = (appointment: AppointmentRow, type: 'view' | 'approve' | 'decline' | 'reschedule') => {
    setSelectedAppointment(appointment);
    setActionType(type);
    setDialogOpen(true);
    setNewDate('');
    setNewTime('');
  };

  const handleConfirm = async () => {
    if (!selectedAppointment) return;

    try {
      if (selectedAppointment.isRequest) {
        if (actionType === 'approve' || actionType === 'decline') {
          await appointmentService.respondAppointmentRequest(selectedAppointment.id, {
            status: actionType === 'approve' ? 'accepted' : 'rejected',
          });
          setRequests((prev) => prev.filter((req) => req.id !== selectedAppointment.id));
          showSuccess(actionType === 'approve' ? 'Request approved.' : 'Request declined.');
        }
      } else if (actionType === 'approve' || actionType === 'decline') {
        await appointmentService.updateMentorAppointmentStatus(selectedAppointment.id, {
          status: actionType === 'approve' ? 'confirmed' : 'cancelled',
        });
        setAppointments((prev) => prev.map((apt) => (
          apt.id === selectedAppointment.id
            ? { ...apt, status: actionType === 'approve' ? 'confirmed' : 'cancelled' }
            : apt
        )));
        showSuccess(actionType === 'approve' ? 'Appointment confirmed.' : 'Appointment cancelled.');
      } else if (actionType === 'reschedule') {
        showError('Rescheduling must be initiated by the student for now.');
      }
    } catch (err: any) {
      showError(err?.response?.data?.error || 'Action failed. Please try again.');
    } finally {
      setDialogOpen(false);
      setSelectedAppointment(null);
    }
  };

  const getStatusChip = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      pending: 'warning',
      confirmed: 'info',
      cancelled: 'error',
      completed: 'success',
      accepted: 'success',
      rejected: 'error',
      expired: 'default',
    };
    return <Chip label={status.charAt(0).toUpperCase() + status.slice(1)} color={colors[status] || 'default'} size="small" />;
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const upcomingAppointments = appointments.filter(a => a.status === 'confirmed' || a.status === 'pending');
  const pastAppointments = appointments.filter(a => a.status === 'completed' || a.status === 'cancelled' || a.status === 'expired');
  const pendingRequests = requests.filter(a => a.status === 'pending');

  let filteredAppointments = tabValue === 0
    ? upcomingAppointments.filter(a => statusFilter === 'all' || a.status === statusFilter)
    : tabValue === 1
    ? pastAppointments.filter(a => statusFilter === 'all' || a.status === statusFilter)
    : pendingRequests;

  if (tabValue === 0 && windowFilter === '24h') {
    const now = new Date();
    const cutoff = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    filteredAppointments = filteredAppointments.filter((apt) => {
      if (!apt.scheduled_at) return false;
      const start = new Date(apt.scheduled_at);
      return start >= now && start <= cutoff;
    });
  }

  if (tabValue === 1 && missingFeedbackOnly) {
    filteredAppointments = filteredAppointments.filter(
      (apt) => apt.status === 'completed' && !apt.mentor_feedback
    );
  }

  if (loading) {
    return <LoadingSpinner message="Loading appointments..." />;
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Appointments
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Manage your mentoring sessions
        </Typography>
      </Box>

      {/* Tabs and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} sx={{ mb: 2 }}>
              <Tab label={`Upcoming (${upcomingAppointments.length})`} />
              <Tab label={`Past (${pastAppointments.length})`} />
              <Tab label={`Requests (${pendingRequests.length})`} />
            </Tabs>
            <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Filter by Status</InputLabel>
            <Select
              value={statusFilter}
              label="Filter by Status"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="all">All Status</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="confirmed">Confirmed</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
              <MenuItem value="cancelled">Cancelled</MenuItem>
            </Select>
          </FormControl>
          {(statusFilter !== 'all' || windowFilter || missingFeedbackOnly) && (
            <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap', alignItems: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Active filters:
              </Typography>
              {statusFilter !== 'all' && (
                <Chip label={`Status: ${statusFilter}`} size="small" />
              )}
              {windowFilter && (
                <Chip label="Next 24h" size="small" color="success" />
              )}
              {missingFeedbackOnly && (
                <Chip label="Missing feedback" size="small" color="error" />
              )}
              <Button
                size="small"
                variant="text"
                onClick={() => {
                  setStatusFilter('all');
                  setWindowFilter(null);
                  setMissingFeedbackOnly(false);
                  navigate('/mentor/appointments', { replace: true });
                }}
              >
                Clear
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Appointments Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Student</TableCell>
                  <TableCell>Session Type</TableCell>
                  <TableCell>Time</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredAppointments.map((appointment) => (
                  <TableRow key={appointment.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Avatar sx={{ mr: 2, width: 32, height: 32 }}>
                          {appointment.student.name.charAt(0)}
                        </Avatar>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {appointment.student.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {appointment.student.email}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip label={appointment.session_type} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDateTime(appointment.scheduled_at)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {appointment.duration} min
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {getStatusChip(appointment.status)}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={() => handleAction(appointment, 'view')}
                        color="primary"
                      >
                        <ViewIcon />
                      </IconButton>
                      {appointment.status === 'pending' && appointment.isRequest && (
                        <>
                          <IconButton
                            size="small"
                            onClick={() => handleAction(appointment, 'approve')}
                            color="success"
                          >
                            <ApproveIcon />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleAction(appointment, 'decline')}
                            color="error"
                          >
                            <DeclineIcon />
                          </IconButton>
                        </>
                      )}
                      {appointment.status === 'confirmed' && !appointment.isRequest && (
                        <IconButton
                          size="small"
                          onClick={() => handleAction(appointment, 'reschedule')}
                          color="primary"
                        >
                          <RescheduleIcon />
                        </IconButton>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Action Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {actionType === 'view' && 'Appointment Details'}
          {actionType === 'approve' && 'Approve Appointment'}
          {actionType === 'decline' && 'Decline Appointment'}
          {actionType === 'reschedule' && 'Reschedule Appointment'}
        </DialogTitle>
        <DialogContent>
          {selectedAppointment && (
            <Box sx={{ pt: 2 }}>
              {actionType === 'view' && (
                <>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">Student</Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {selectedAppointment.student.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {selectedAppointment.student.email}
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">Session Type</Typography>
                    <Typography variant="body1">
                      {selectedAppointment.session_type}
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">Scheduled Time</Typography>
                    <Typography variant="body1">
                      {formatDateTime(selectedAppointment.scheduled_at)}
                    </Typography>
                  </Box>
                </>
              )}
              {actionType === 'reschedule' && (
                <>
                  <TextField
                    fullWidth
                    type="date"
                    label="New Date"
                    value={newDate}
                    onChange={(e) => setNewDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    sx={{ mb: 2 }}
                    required
                  />
                  <TextField
                    fullWidth
                    type="time"
                    label="New Time"
                    value={newTime}
                    onChange={(e) => setNewTime(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    required
                  />
                </>
              )}
              {(actionType === 'approve' || actionType === 'decline') && (
                <Alert severity={actionType === 'approve' ? 'info' : 'warning'} sx={{ mb: 2 }}>
                  {actionType === 'approve'
                    ? 'Are you sure you want to approve this appointment?'
                    : 'Are you sure you want to decline this appointment? The student will be notified.'}
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          {actionType !== 'view' && (
            <Button
              variant="contained"
              onClick={handleConfirm}
              color={actionType === 'decline' ? 'error' : 'primary'}
              disabled={actionType === 'reschedule' && (!newDate || !newTime)}
            >
              {actionType === 'approve' ? 'Approve' : actionType === 'decline' ? 'Decline' : 'Reschedule'}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MentorAppointmentsPage;
