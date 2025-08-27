import React, { useState, useEffect } from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Box,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  Alert,
  Avatar,
  Grid,
} from '@mui/material';
import {
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  FilterList as FilterIcon,
  Event as EventIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';

import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import SkeletonLoader from '../../components/common/SkeletonLoader';
import adminService from '../../services/api/adminService';

interface Appointment {
  id: number;
  student: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    profile_picture?: string;
  };
  mentor: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    profile_picture?: string;
    expertise_areas: string[];
  };
  status: 'scheduled' | 'completed' | 'cancelled' | 'no_show';
  scheduled_at: string;
  duration: number; // in minutes
  topic: string;
  notes?: string;
  meeting_link?: string;
  created_at: string;
  updated_at: string;
  payment_status: 'pending' | 'completed' | 'refunded';
  amount: number;
}

const AppointmentManagementPage: React.FC = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [paymentFilter, setPaymentFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState<'view' | 'edit' | 'delete' | 'cancel'>('view');

  useEffect(() => {
    fetchAppointments();
  }, [page, searchTerm, statusFilter, paymentFilter]);

  const fetchAppointments = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual appointments API
      // For now, we'll use mock data since the backend doesn't have a specific appointments endpoint
      const mockAppointments: Appointment[] = [
        {
          id: 1,
          student: {
            id: 1,
            username: 'john_student',
            email: 'john.student@example.com',
            first_name: 'John',
            last_name: 'Student',
          },
          mentor: {
            id: 2,
            username: 'jane_mentor',
            email: 'jane.mentor@example.com',
            first_name: 'Jane',
            last_name: 'Mentor',
            expertise_areas: ['React', 'Node.js'],
          },
          status: 'scheduled',
          scheduled_at: '2024-01-25T10:00:00Z',
          duration: 60,
          topic: 'React Best Practices',
          notes: 'Student wants to learn about React hooks and state management',
          meeting_link: 'https://meet.google.com/abc-defg-hij',
          created_at: '2024-01-20T15:30:00Z',
          updated_at: '2024-01-20T15:30:00Z',
          payment_status: 'completed',
          amount: 50.00,
        },
        {
          id: 2,
          student: {
            id: 3,
            username: 'bob_student',
            email: 'bob.student@example.com',
            first_name: 'Bob',
            last_name: 'Student',
          },
          mentor: {
            id: 4,
            username: 'alice_mentor',
            email: 'alice.mentor@example.com',
            first_name: 'Alice',
            last_name: 'Mentor',
            expertise_areas: ['Python', 'Data Science'],
          },
          status: 'completed',
          scheduled_at: '2024-01-24T14:00:00Z',
          duration: 90,
          topic: 'Python Data Analysis',
          notes: 'Completed successfully, student was very satisfied',
          created_at: '2024-01-19T10:15:00Z',
          updated_at: '2024-01-24T15:30:00Z',
          payment_status: 'completed',
          amount: 75.00,
        },
        {
          id: 3,
          student: {
            id: 5,
            username: 'sarah_student',
            email: 'sarah.student@example.com',
            first_name: 'Sarah',
            last_name: 'Student',
          },
          mentor: {
            id: 2,
            username: 'jane_mentor',
            email: 'jane.mentor@example.com',
            first_name: 'Jane',
            last_name: 'Mentor',
            expertise_areas: ['React', 'Node.js'],
          },
          status: 'cancelled',
          scheduled_at: '2024-01-23T16:00:00Z',
          duration: 60,
          topic: 'Node.js Backend Development',
          notes: 'Cancelled by student due to emergency',
          created_at: '2024-01-18T12:00:00Z',
          updated_at: '2024-01-22T09:00:00Z',
          payment_status: 'refunded',
          amount: 50.00,
        },
      ];
      setAppointments(mockAppointments);
      setTotalPages(1);
    } catch (err) {
      setError('Failed to load appointments');
      console.error('Error fetching appointments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    setPage(1);
  };

  const handleStatusFilterChange = (event: any) => {
    setStatusFilter(event.target.value);
    setPage(1);
  };

  const handlePaymentFilterChange = (event: any) => {
    setPaymentFilter(event.target.value);
    setPage(1);
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const handleAppointmentAction = (appointment: Appointment, action: 'view' | 'edit' | 'delete' | 'cancel') => {
    setSelectedAppointment(appointment);
    setDialogType(action);
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    setSelectedAppointment(null);
  };

  const handleConfirmAction = async () => {
    if (!selectedAppointment) return;

    try {
      switch (dialogType) {
        case 'edit':
          // TODO: Implement edit appointment
          console.log('Edit appointment:', selectedAppointment.id);
          break;
        case 'delete':
          // TODO: Implement delete appointment
          console.log('Delete appointment:', selectedAppointment.id);
          break;
        case 'cancel':
          // TODO: Implement cancel appointment
          console.log('Cancel appointment:', selectedAppointment.id);
          break;
      }
      handleDialogClose();
      fetchAppointments(); // Refresh the list
    } catch (err) {
      console.error('Error performing action:', err);
    }
  };

  const getStatusChip = (status: string) => {
    switch (status) {
      case 'scheduled':
        return <Chip label="Scheduled" color="primary" size="small" />;
      case 'completed':
        return <Chip label="Completed" color="success" size="small" />;
      case 'cancelled':
        return <Chip label="Cancelled" color="error" size="small" />;
      case 'no_show':
        return <Chip label="No Show" color="warning" size="small" />;
      default:
        return <Chip label={status} color="default" size="small" />;
    }
  };

  const getPaymentChip = (status: string) => {
    switch (status) {
      case 'pending':
        return <Chip label="Pending" color="warning" size="small" />;
      case 'completed':
        return <Chip label="Paid" color="success" size="small" />;
      case 'refunded':
        return <Chip label="Refunded" color="info" size="small" />;
      default:
        return <Chip label={status} color="default" size="small" />;
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  if (loading && appointments.length === 0) {
    return <LoadingSpinner message="Loading appointments..." />;
  }

  return (
    <>
      <PageHeader
        title="Appointment Management"
        breadcrumbs={[
          { label: 'Admin', path: '/admin' },
          { label: 'Appointments', path: '/admin/appointments' },
        ]}
      />

      <Container maxWidth="xl">
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
              <TextField
                placeholder="Search appointments..."
                value={searchTerm}
                onChange={handleSearch}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
                sx={{ minWidth: 300 }}
              />
              <FormControl sx={{ minWidth: 150 }}>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={handleStatusFilterChange}
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="scheduled">Scheduled</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="cancelled">Cancelled</MenuItem>
                  <MenuItem value="no_show">No Show</MenuItem>
                </Select>
              </FormControl>
              <FormControl sx={{ minWidth: 150 }}>
                <InputLabel>Payment</InputLabel>
                <Select
                  value={paymentFilter}
                  label="Payment"
                  onChange={handlePaymentFilterChange}
                >
                  <MenuItem value="all">All Payments</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="refunded">Refunded</MenuItem>
                </Select>
              </FormControl>
              <Button
                variant="contained"
                startIcon={<FilterIcon />}
                onClick={() => {/* TODO: Implement advanced filters */}}
              >
                Advanced Filters
              </Button>
            </Box>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Appointments ({appointments.length})</Typography>
            </Box>

            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Student</TableCell>
                    <TableCell>Mentor</TableCell>
                    <TableCell>Topic</TableCell>
                    <TableCell>Date & Time</TableCell>
                    <TableCell>Duration</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Payment</TableCell>
                    <TableCell>Amount</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={9}>
                        <SkeletonLoader type="table" count={3} />
                      </TableCell>
                    </TableRow>
                  ) : (
                    appointments.map((appointment) => (
                      <TableRow key={appointment.id} hover>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Avatar sx={{ mr: 2, width: 32, height: 32 }}>
                              {appointment.student.first_name.charAt(0)}
                            </Avatar>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {appointment.student.first_name} {appointment.student.last_name}
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
                              {appointment.mentor.first_name.charAt(0)}
                            </Avatar>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {appointment.mentor.first_name} {appointment.mentor.last_name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {appointment.mentor.expertise_areas.slice(0, 2).join(', ')}
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                            {appointment.topic}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDateTime(appointment.scheduled_at)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDuration(appointment.duration)}
                          </Typography>
                        </TableCell>
                        <TableCell>{getStatusChip(appointment.status)}</TableCell>
                        <TableCell>{getPaymentChip(appointment.payment_status)}</TableCell>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            ${appointment.amount.toFixed(2)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={() => handleAppointmentAction(appointment, 'view')}
                            color="primary"
                          >
                            <ViewIcon />
                          </IconButton>
                          {appointment.status === 'scheduled' && (
                            <>
                              <IconButton
                                size="small"
                                onClick={() => handleAppointmentAction(appointment, 'edit')}
                                color="primary"
                              >
                                <EditIcon />
                              </IconButton>
                              <IconButton
                                size="small"
                                onClick={() => handleAppointmentAction(appointment, 'cancel')}
                                color="warning"
                              >
                                <CancelIcon />
                              </IconButton>
                            </>
                          )}
                          <IconButton
                            size="small"
                            onClick={() => handleAppointmentAction(appointment, 'delete')}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>

            {totalPages > 1 && (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                <Pagination
                  count={totalPages}
                  page={page}
                  onChange={handlePageChange}
                  color="primary"
                />
              </Box>
            )}
          </CardContent>
        </Card>
      </Container>

      {/* Appointment Detail Dialog */}
      <Dialog open={dialogOpen} onClose={handleDialogClose} maxWidth="md" fullWidth>
        <DialogTitle>
          {dialogType === 'view' && 'Appointment Details'}
          {dialogType === 'edit' && 'Edit Appointment'}
          {dialogType === 'delete' && 'Delete Appointment'}
          {dialogType === 'cancel' && 'Cancel Appointment'}
        </DialogTitle>
        <DialogContent>
          {selectedAppointment && (
            <Box>
              {dialogType === 'view' && (
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>
                      Student Information
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Avatar sx={{ mr: 2, width: 48, height: 48 }}>
                        {selectedAppointment.student.first_name.charAt(0)}
                      </Avatar>
                      <Box>
                        <Typography variant="body1" fontWeight="medium">
                          {selectedAppointment.student.first_name} {selectedAppointment.student.last_name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {selectedAppointment.student.email}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>
                      Mentor Information
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Avatar sx={{ mr: 2, width: 48, height: 48 }}>
                        {selectedAppointment.mentor.first_name.charAt(0)}
                      </Avatar>
                      <Box>
                        <Typography variant="body1" fontWeight="medium">
                          {selectedAppointment.mentor.first_name} {selectedAppointment.mentor.last_name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {selectedAppointment.mentor.email}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="h6" gutterBottom>
                      Appointment Details
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        <strong>Topic:</strong> {selectedAppointment.topic}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        <strong>Date & Time:</strong> {formatDateTime(selectedAppointment.scheduled_at)}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        <strong>Duration:</strong> {formatDuration(selectedAppointment.duration)}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        <strong>Status:</strong> {getStatusChip(selectedAppointment.status)}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        <strong>Payment Status:</strong> {getPaymentChip(selectedAppointment.payment_status)}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        <strong>Amount:</strong> ${selectedAppointment.amount.toFixed(2)}
                      </Typography>
                      {selectedAppointment.notes && (
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>Notes:</strong> {selectedAppointment.notes}
                        </Typography>
                      )}
                      {selectedAppointment.meeting_link && (
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>Meeting Link:</strong>{' '}
                          <Button
                            size="small"
                            href={selectedAppointment.meeting_link}
                            target="_blank"
                            startIcon={<EventIcon />}
                          >
                            Join Meeting
                          </Button>
                        </Typography>
                      )}
                    </Box>
                  </Grid>
                </Grid>
              )}

              {dialogType === 'delete' && (
                <Typography>
                  Are you sure you want to delete this appointment? This action cannot be undone.
                </Typography>
              )}

              {dialogType === 'cancel' && (
                <Typography>
                  Are you sure you want to cancel this appointment? The student will be notified.
                </Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>Cancel</Button>
          {dialogType === 'delete' && (
            <Button onClick={handleConfirmAction} color="error" variant="contained">
              Delete
            </Button>
          )}
          {dialogType === 'cancel' && (
            <Button onClick={handleConfirmAction} color="warning" variant="contained">
              Cancel Appointment
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </>
  );
};

export default AppointmentManagementPage; 