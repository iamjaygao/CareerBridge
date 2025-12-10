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

interface Appointment {
  id: number;
  student: {
    name: string;
    email: string;
    avatar?: string;
  };
  session_type: string;
  scheduled_at: string;
  duration: number;
  status: 'pending' | 'confirmed' | 'canceled' | 'completed';
}

const MentorAppointmentsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [tabValue, setTabValue] = useState(0);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'view' | 'approve' | 'decline' | 'reschedule'>('view');
  const [newDate, setNewDate] = useState('');
  const [newTime, setNewTime] = useState('');

  useEffect(() => {
    setTimeout(() => {
      setAppointments([
        {
          id: 1,
          student: { name: 'Alice Johnson', email: 'alice@example.com' },
          session_type: 'Career Chat',
          scheduled_at: '2025-01-20T14:00:00Z',
          duration: 60,
          status: 'confirmed',
        },
        {
          id: 2,
          student: { name: 'Bob Smith', email: 'bob@example.com' },
          session_type: 'Resume Review',
          scheduled_at: '2025-01-20T16:00:00Z',
          duration: 45,
          status: 'pending',
        },
        {
          id: 3,
          student: { name: 'Charlie Brown', email: 'charlie@example.com' },
          session_type: 'Mock Interview',
          scheduled_at: '2025-01-18T10:00:00Z',
          duration: 60,
          status: 'completed',
        },
        {
          id: 4,
          student: { name: 'Diana Prince', email: 'diana@example.com' },
          session_type: 'Career Chat',
          scheduled_at: '2025-01-19T15:00:00Z',
          duration: 45,
          status: 'canceled',
        },
      ]);
      setLoading(false);
    }, 500);
  }, []);

  const handleAction = (appointment: Appointment, type: 'view' | 'approve' | 'decline' | 'reschedule') => {
    setSelectedAppointment(appointment);
    setActionType(type);
    setDialogOpen(true);
    setNewDate('');
    setNewTime('');
  };

  const handleConfirm = () => {
    if (!selectedAppointment) return;

    if (actionType === 'approve') {
      setAppointments(appointments.map(app =>
        app.id === selectedAppointment.id
          ? { ...app, status: 'confirmed' as const }
          : app
      ));
    } else if (actionType === 'decline') {
      setAppointments(appointments.map(app =>
        app.id === selectedAppointment.id
          ? { ...app, status: 'canceled' as const }
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
      pending: 'warning',
      confirmed: 'info',
      canceled: 'error',
      completed: 'success',
    };
    return <Chip label={status.charAt(0).toUpperCase() + status.slice(1)} color={colors[status] || 'default'} size="small" />;
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const upcomingAppointments = appointments.filter(a => a.status === 'confirmed' || a.status === 'pending');
  const pastAppointments = appointments.filter(a => a.status === 'completed' || a.status === 'canceled');
  const pendingRequests = appointments.filter(a => a.status === 'pending');

  const filteredAppointments = tabValue === 0
    ? upcomingAppointments.filter(a => statusFilter === 'all' || a.status === statusFilter)
    : tabValue === 1
    ? pastAppointments.filter(a => statusFilter === 'all' || a.status === statusFilter)
    : pendingRequests;

  if (loading) {
    return <LoadingSpinner message="Loading appointments..." />;
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
              <MenuItem value="canceled">Canceled</MenuItem>
            </Select>
          </FormControl>
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
                      {appointment.status === 'pending' && (
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
                      {appointment.status === 'confirmed' && (
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

