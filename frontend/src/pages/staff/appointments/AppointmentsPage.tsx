import React, { useState, useEffect } from 'react';
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
  Alert,
} from '@mui/material';
import {
  Block as NoShowIcon,
  Cancel as CancelIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../../components/common/LoadingSpinner';
import adminService from '../../../services/api/adminService';
import { useNotification } from '../../../components/common/NotificationProvider';

interface Appointment {
  id: number;
  student: {
    name: string;
    email: string;
  };
  mentor: {
    name: string;
    email: string;
  };
  scheduled_at: string;
  duration: number;
  status: string;
  topic: string;
}

const AppointmentsPage: React.FC = () => {
  const { showSuccess, showError } = useNotification();
  const [loading, setLoading] = useState(true);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'view' | 'cancel' | 'no_show'>('view');
  const [cancelReason, setCancelReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        const data = await adminService.getStaffAppointments();
        const list = Array.isArray(data) ? data : (data?.results || []);
        const mapped = list.map((apt: any) => {
          const studentName = apt.student
            ? `${apt.student.first_name || ''} ${apt.student.last_name || ''}`.trim() || apt.student.username
            : apt.user_username || 'Student';
          const mentorName = apt.mentor
            ? `${apt.mentor.first_name || ''} ${apt.mentor.last_name || ''}`.trim() || apt.mentor.username
            : apt.mentor_name || 'Mentor';
          return {
            id: apt.id || apt.appointment_id,
            student: {
              name: studentName,
              email: apt.student?.email || '',
            },
            mentor: {
              name: mentorName,
              email: apt.mentor?.email || '',
            },
            scheduled_at: apt.scheduled_at || apt.scheduled_start,
            duration: apt.duration || 60,
            status: apt.status || 'pending',
            topic: apt.topic || apt.title || 'Session',
          };
        });
        setAppointments(mapped);
      } catch {
        setAppointments([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAppointments();
  }, []);

  const handleAction = (appointment: Appointment, type: 'view' | 'cancel' | 'no_show' = 'view') => {
    setSelectedAppointment(appointment);
    setActionType(type);
    setCancelReason('');
    setDialogOpen(true);
  };

  const handleConfirm = async () => {
    if (!selectedAppointment) return;

    if (actionType === 'view') {
      showSuccess('Appointment details loaded.');
      setDialogOpen(false);
      setSelectedAppointment(null);
      return;
    }

    try {
      setActionLoading(true);
      const payload: any = {
        status: actionType === 'cancel' ? 'cancelled' : 'no_show',
      };
      if (actionType === 'cancel' && cancelReason.trim()) {
        payload.cancellation_reason = cancelReason.trim();
      }
      const updated = await adminService.updateStaffAppointment(selectedAppointment.id, payload);
      setAppointments(prev =>
        prev.map(apt =>
          apt.id === selectedAppointment.id
            ? { ...apt, status: updated?.status || payload.status }
            : apt
        )
      );
      showSuccess(actionType === 'cancel' ? 'Appointment cancelled.' : 'Marked as no-show.');
      setDialogOpen(false);
      setSelectedAppointment(null);
    } catch {
      showError('Failed to update appointment.');
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusChip = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      pending: 'warning',
      confirmed: 'info',
      scheduled: 'info',
      completed: 'success',
      cancelled: 'error',
      conflict: 'warning',
      expired: 'default',
      no_show: 'default',
    };
    return <Chip label={status.charAt(0).toUpperCase() + status.slice(1)} color={colors[status] || 'default'} size="small" />;
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading) {
    return <LoadingSpinner message="Loading appointments..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Appointment Management
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Manage appointments and resolve conflicts
        </Typography>
      </Box>

      {/* Appointments Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Student</TableCell>
                  <TableCell>Mentor</TableCell>
                  <TableCell>Time</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Topic</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {appointments.map((appointment) => (
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
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Avatar sx={{ mr: 2, width: 32, height: 32 }}>
                          {appointment.mentor.name.charAt(0)}
                        </Avatar>
                        <Typography variant="body2" fontWeight="medium">
                          {appointment.mentor.name}
                        </Typography>
                      </Box>
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
                      <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                        {appointment.topic}
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
                      {(appointment.status === 'pending' || appointment.status === 'confirmed') && (
                        <IconButton
                          size="small"
                          onClick={() => handleAction(appointment, 'cancel')}
                          color="error"
                        >
                          <CancelIcon />
                        </IconButton>
                      )}
                      {appointment.status === 'confirmed' && (
                        <IconButton
                          size="small"
                          onClick={() => handleAction(appointment, 'no_show')}
                          color="warning"
                        >
                          <NoShowIcon />
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
          {actionType === 'cancel' && 'Cancel Appointment'}
          {actionType === 'no_show' && 'Mark No-Show'}
        </DialogTitle>
        <DialogContent>
          {selectedAppointment && (
            <Box sx={{ pt: 2 }}>
              <>
                {actionType === 'cancel' && (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    Cancelling will notify the student and mentor.
                  </Alert>
                )}
                {actionType === 'no_show' && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    Mark this appointment as no-show.
                  </Alert>
                )}
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
                  <Typography variant="body2" color="text.secondary">Mentor</Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {selectedAppointment.mentor.name}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Scheduled Time</Typography>
                  <Typography variant="body1">
                    {formatDateTime(selectedAppointment.scheduled_at)}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Topic</Typography>
                  <Typography variant="body1">
                    {selectedAppointment.topic}
                  </Typography>
                </Box>
                {actionType === 'cancel' && (
                  <TextField
                    fullWidth
                    label="Cancellation reason"
                    value={cancelReason}
                    onChange={(e) => setCancelReason(e.target.value)}
                    multiline
                    minRows={2}
                  />
                )}
              </>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
          <Button
            variant="contained"
            onClick={handleConfirm}
            disabled={actionLoading}
            color={actionType === 'cancel' ? 'error' : 'primary'}
          >
            {actionType === 'view' ? 'Done' : actionType === 'cancel' ? 'Cancel Appointment' : 'Mark No-Show'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AppointmentsPage;
