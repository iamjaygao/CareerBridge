import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { useRole } from '../../contexts/RoleContext';
import adminService from '../../services/api/adminService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import { handleApiError } from '../../services/utils/errorHandler';
import type { ApiError } from '../../services/utils/errorHandler';

const AppointmentsPage: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const { isSuperAdmin } = useRole();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [appointments, setAppointments] = useState<any[]>([]);

  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await adminService.getAppointments();
        
        // Handle different response formats
        let appointmentsList: any[] = [];
        if (Array.isArray(data)) {
          appointmentsList = data;
        } else if (data.results && Array.isArray(data.results)) {
          appointmentsList = data.results;
        } else if (data.data && Array.isArray(data.data)) {
          appointmentsList = data.data;
        }
        
        // Normalize appointment objects
        const normalizedAppointments = appointmentsList.map((apt: any) => ({
          id: apt.id || apt.appointment_id,
          student: apt.student
            ? `${apt.student.first_name || ''} ${apt.student.last_name || ''}`.trim() || apt.student.username
            : apt.student_name || apt.student || 'Unknown',
          mentor: apt.mentor
            ? `${apt.mentor.first_name || ''} ${apt.mentor.last_name || ''}`.trim() || apt.mentor.username
            : apt.mentor_name || apt.mentor || 'Unknown',
          date: apt.scheduled_at
            ? new Date(apt.scheduled_at).toLocaleDateString()
            : (apt.scheduled_start ? new Date(apt.scheduled_start).toLocaleDateString() : (apt.date || 'N/A')),
          status: apt.status || 'pending',
        }));
        
        setAppointments(normalizedAppointments);
      } catch (err: any) {
        setError(handleApiError(err));
        console.error('Failed to fetch appointments:', err);
        setAppointments([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAppointments();
  }, []);

  if (!isSuperAdmin) {
    return null;
  }

  if (loading) {
    return <LoadingSpinner message="Loading appointments..." />;
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
          Appointment Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          View and manage all appointments
        </Typography>
      </Box>

      {error && (
        <ErrorAlert error={error} overrideMessage="Failed to load appointments." />
      )}

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Student</TableCell>
                <TableCell>Mentor</TableCell>
                <TableCell>Date</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {appointments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No appointments found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                appointments.map((apt) => (
                  <TableRow key={apt.id}>
                    <TableCell>{apt.id}</TableCell>
                    <TableCell>{apt.student}</TableCell>
                    <TableCell>{apt.mentor}</TableCell>
                    <TableCell>{apt.date}</TableCell>
                    <TableCell>
                      <Chip
                        label={apt.status}
                        size="small"
                        color={apt.status === 'confirmed' ? 'success' : 'warning'}
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton size="small">
                        <EditIcon />
                      </IconButton>
                      <IconButton size="small" color="error">
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Container>
  );
};

export default AppointmentsPage;
