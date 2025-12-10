import React, { useState, useEffect } from 'react';
import {
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
      setError(null);
      
      // Build query parameters
      const params: any = {
        page: page,
      };
      
      if (searchTerm) {
        params.search = searchTerm;
      }
      
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }
      
      if (paymentFilter !== 'all') {
        params.payment_status = paymentFilter;
      }
      
      const data = await adminService.getAppointments(params);
      
      // Handle different response formats
      let appointmentsData: Appointment[] = [];
      if (Array.isArray(data)) {
        appointmentsData = data;
        setTotalPages(1);
      } else if (data.results && Array.isArray(data.results)) {
        appointmentsData = data.results;
        setTotalPages(data.total_pages || Math.ceil((data.count || 0) / (data.page_size || 10)) || 1);
      } else if (data.data && Array.isArray(data.data)) {
        appointmentsData = data.data;
        setTotalPages(data.total_pages || 1);
      } else {
        console.warn('Unexpected appointments response format:', data);
        appointmentsData = [];
        setTotalPages(1);
      }
      
      setAppointments(appointmentsData);
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail 
        || err?.response?.data?.error
        || err?.message 
        || 'Failed to load appointments';
      setError(errorMessage);
      console.error('Error fetching appointments:', err);
      // Set empty array on error to prevent showing stale mock data
      setAppointments([]);
      setTotalPages(1);
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
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Appointment Management
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Manage all appointments and sessions
        </Typography>
      </Box>

      <Box>
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
                              {typeof appointment.mentor === 'object' 
                                ? (appointment.mentor as any).user 
                                  ? ((appointment.mentor as any).user.first_name?.[0] || (appointment.mentor as any).user.username?.[0] || 'M')
                                  : ((appointment.mentor as any).first_name?.[0] || (appointment.mentor as any).username?.[0] || 'M')
                                : 'M'}
                            </Avatar>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {typeof appointment.mentor === 'object' 
                                  ? (appointment.mentor as any).user
                                    ? `${(appointment.mentor as any).user.first_name || ''} ${(appointment.mentor as any).user.last_name || ''}`.trim() || (appointment.mentor as any).user.username
                                    : `${(appointment.mentor as any).first_name || ''} ${(appointment.mentor as any).last_name || ''}`.trim() || (appointment.mentor as any).username
                                  : 'Mentor'}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {typeof appointment.mentor === 'object' && appointment.mentor.expertise_areas
                                  ? appointment.mentor.expertise_areas.slice(0, 2).join(', ')
                                  : 'N/A'}
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
      </Box>

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
                        {typeof selectedAppointment.mentor === 'object' 
                          ? (selectedAppointment.mentor as any).user
                            ? ((selectedAppointment.mentor as any).user.first_name?.[0] || (selectedAppointment.mentor as any).user.username?.[0] || 'M')
                            : ((selectedAppointment.mentor as any).first_name?.[0] || (selectedAppointment.mentor as any).username?.[0] || 'M')
                          : 'M'}
                      </Avatar>
                      <Box>
                        <Typography variant="body1" fontWeight="medium">
                          {typeof selectedAppointment.mentor === 'object' 
                            ? (selectedAppointment.mentor as any).user
                              ? `${(selectedAppointment.mentor as any).user.first_name || ''} ${(selectedAppointment.mentor as any).user.last_name || ''}`.trim() || (selectedAppointment.mentor as any).user.username
                              : `${(selectedAppointment.mentor as any).first_name || ''} ${(selectedAppointment.mentor as any).last_name || ''}`.trim() || (selectedAppointment.mentor as any).username
                            : 'Mentor'}
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