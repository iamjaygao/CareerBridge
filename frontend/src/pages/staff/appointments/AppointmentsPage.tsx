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
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Alert,
} from '@mui/material';
import {
  Edit as EditIcon,
  Cancel as CancelIcon,
  Event as EventIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../../components/common/LoadingSpinner';

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
  status: 'scheduled' | 'completed' | 'cancelled' | 'conflict';
  topic: string;
}

const AppointmentsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'view' | 'reschedule' | 'cancel' | 'resolve'>('view');
  const [newDate, setNewDate] = useState('');
  const [newTime, setNewTime] = useState('');

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setAppointments([
        {
          id: 1,
          student: { name: 'Alice Johnson', email: 'alice@example.com' },
          mentor: { name: 'John Doe', email: 'john@example.com' },
          scheduled_at: '2025-01-20T14:00:00Z',
          duration: 60,
          status: 'scheduled',
          topic: 'Career Transition Advice',
        },
        {
          id: 2,
          student: { name: 'Bob Smith', email: 'bob@example.com' },
          mentor: { name: 'Jane Smith', email: 'jane@example.com' },
          scheduled_at: '2025-01-20T15:30:00Z',
          duration: 45,
          status: 'conflict',
          topic: 'Technical Interview Prep',
        },
        {
          id: 3,
          student: { name: 'Charlie Brown', email: 'charlie@example.com' },
          mentor: { name: 'John Doe', email: 'john@example.com' },
          scheduled_at: '2025-01-19T10:00:00Z',
          duration: 60,
          status: 'completed',
          topic: 'Resume Review',
        },
      ]);
      setLoading(false);
    }, 500);
  }, []);

  const handleAction = (appointment: Appointment, type: 'view' | 'reschedule' | 'cancel' | 'resolve') => {
    setSelectedAppointment(appointment);
    setActionType(type);
    setDialogOpen(true);
    setNewDate('');
    setNewTime('');
  };

  const handleConfirm = () => {
    if (!selectedAppointment) return;

    // Update appointment
    if (actionType === 'cancel') {
      setAppointments(appointments.map(app => 
        app.id === selectedAppointment.id 
          ? { ...app, status: 'cancelled' as const }
          : app
      ));
    } else if (actionType === 'resolve') {
      setAppointments(appointments.map(app => 
        app.id === selectedAppointment.id 
          ? { ...app, status: 'scheduled' as const }
          : app
      ));
    } else if (actionType === 'reschedule' && newDate && newTime) {
      setAppointments(appointments.map(app => 
        app.id === selectedAppointment.id 
          ? { ...app, scheduled_at: `${newDate}T${newTime}:00Z` }
          : app
      ));
    }

    setDialogOpen(false);
    setSelectedAppointment(null);
  };

  const getStatusChip = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      scheduled: 'info',
      completed: 'success',
      cancelled: 'error',
      conflict: 'warning',
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
                      {appointment.status === 'scheduled' && (
                        <IconButton
                          size="small"
                          onClick={() => handleAction(appointment, 'reschedule')}
                          color="primary"
                        >
                          <EditIcon />
                        </IconButton>
                      )}
                      {appointment.status === 'conflict' && (
                        <IconButton
                          size="small"
                          onClick={() => handleAction(appointment, 'resolve')}
                          color="success"
                        >
                          <EventIcon />
                        </IconButton>
                      )}
                      {appointment.status !== 'cancelled' && appointment.status !== 'completed' && (
                        <IconButton
                          size="small"
                          onClick={() => handleAction(appointment, 'cancel')}
                          color="error"
                        >
                          <CancelIcon />
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
          {actionType === 'reschedule' && 'Reschedule Appointment'}
          {actionType === 'cancel' && 'Cancel Appointment'}
          {actionType === 'resolve' && 'Resolve Conflict'}
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
              {actionType === 'cancel' && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  Are you sure you want to cancel this appointment? This action cannot be undone.
                </Alert>
              )}
              {actionType === 'resolve' && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  Resolve the scheduling conflict and mark this appointment as scheduled.
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
              color={actionType === 'cancel' ? 'error' : 'primary'}
              disabled={actionType === 'reschedule' && (!newDate || !newTime)}
            >
              {actionType === 'reschedule' ? 'Reschedule' : actionType === 'cancel' ? 'Cancel Appointment' : 'Resolve'}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AppointmentsPage;

