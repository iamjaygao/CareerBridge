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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Assignment as AssignIcon,
  CheckCircle as ResolveIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../../components/common/LoadingSpinner';

interface SupportTicket {
  id: number;
  user: {
    name: string;
    email: string;
  };
  issue: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  assigned_staff?: string;
  created_at: string;
}

const UserSupportPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [assignedStaff, setAssignedStaff] = useState('');

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setTickets([
        {
          id: 1,
          user: { name: 'Alice Johnson', email: 'alice@example.com' },
          issue: 'Cannot upload resume',
          description: 'Getting error when trying to upload PDF resume file...',
          priority: 'high',
          status: 'open',
          created_at: '2025-01-15T10:00:00Z',
        },
        {
          id: 2,
          user: { name: 'Bob Smith', email: 'bob@example.com' },
          issue: 'Payment not processing',
          description: 'Credit card payment failed multiple times...',
          priority: 'urgent',
          status: 'in_progress',
          assigned_staff: 'Staff Member 1',
          created_at: '2025-01-14T14:30:00Z',
        },
        {
          id: 3,
          user: { name: 'Charlie Brown', email: 'charlie@example.com' },
          issue: 'Account verification issue',
          description: 'Email verification link not working...',
          priority: 'medium',
          status: 'resolved',
          assigned_staff: 'Staff Member 2',
          created_at: '2025-01-13T09:15:00Z',
        },
      ]);
      setLoading(false);
    }, 500);
  }, []);

  const handleView = (ticket: SupportTicket) => {
    setSelectedTicket(ticket);
    setAssignedStaff(ticket.assigned_staff || '');
    setDialogOpen(true);
  };

  const handleAssign = () => {
    if (!selectedTicket) return;
    setTickets(tickets.map(t => 
      t.id === selectedTicket.id 
        ? { ...t, assigned_staff: assignedStaff, status: 'in_progress' as const }
        : t
    ));
    setDialogOpen(false);
  };

  const handleResolve = (id: number) => {
    setTickets(tickets.map(t => 
      t.id === id 
        ? { ...t, status: 'resolved' as const }
        : t
    ));
  };

  const getPriorityChip = (priority: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      low: 'default',
      medium: 'info',
      high: 'warning',
      urgent: 'error',
    };
    return <Chip label={priority.charAt(0).toUpperCase() + priority.slice(1)} color={colors[priority] || 'default'} size="small" />;
  };

  const getStatusChip = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      open: 'warning',
      in_progress: 'info',
      resolved: 'success',
      closed: 'default',
    };
    return <Chip label={status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')} color={colors[status] || 'default'} size="small" />;
  };

  if (loading) {
    return <LoadingSpinner message="Loading support tickets..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          User Support
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Manage user support tickets and issues
        </Typography>
      </Box>

      {/* Stats Cards */}
      <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
        <Card sx={{ flex: 1, minWidth: 150 }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {tickets.filter(t => t.status === 'open').length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Open Tickets
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1, minWidth: 150 }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {tickets.filter(t => t.status === 'in_progress').length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              In Progress
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1, minWidth: 150 }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {tickets.filter(t => t.priority === 'urgent').length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Urgent Priority
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Tickets Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell>Issue</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Assigned To</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {tickets.map((ticket) => (
                  <TableRow key={ticket.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Avatar sx={{ mr: 2, width: 32, height: 32 }}>
                          {ticket.user.name.charAt(0)}
                        </Avatar>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {ticket.user.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {ticket.user.email}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                        {ticket.issue}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {getPriorityChip(ticket.priority)}
                    </TableCell>
                    <TableCell>
                      {getStatusChip(ticket.status)}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {ticket.assigned_staff || 'Unassigned'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={() => handleView(ticket)}
                        color="primary"
                      >
                        <ViewIcon />
                      </IconButton>
                      {ticket.status !== 'resolved' && ticket.status !== 'closed' && (
                        <IconButton
                          size="small"
                          onClick={() => handleResolve(ticket.id)}
                          color="success"
                        >
                          <ResolveIcon />
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

      {/* Ticket Detail Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Ticket Details</DialogTitle>
        <DialogContent>
          {selectedTicket && (
            <Box sx={{ pt: 2 }}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">User</Typography>
                <Typography variant="body1" fontWeight="medium">
                  {selectedTicket.user.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedTicket.user.email}
                </Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">Issue</Typography>
                <Typography variant="body1" fontWeight="medium">
                  {selectedTicket.issue}
                </Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">Description</Typography>
                <Typography variant="body1" sx={{ mt: 0.5 }}>
                  {selectedTicket.description}
                </Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">Priority</Typography>
                {getPriorityChip(selectedTicket.priority)}
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">Status</Typography>
                {getStatusChip(selectedTicket.status)}
              </Box>
              {!selectedTicket.assigned_staff && (
                <FormControl fullWidth sx={{ mt: 2 }}>
                  <InputLabel>Assign To</InputLabel>
                  <Select
                    value={assignedStaff}
                    label="Assign To"
                    onChange={(e) => setAssignedStaff(e.target.value)}
                  >
                    <MenuItem value="Staff Member 1">Staff Member 1</MenuItem>
                    <MenuItem value="Staff Member 2">Staff Member 2</MenuItem>
                    <MenuItem value="Staff Member 3">Staff Member 3</MenuItem>
                  </Select>
                </FormControl>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
          {!selectedTicket?.assigned_staff && (
            <Button
              variant="contained"
              onClick={handleAssign}
              disabled={!assignedStaff}
              startIcon={<AssignIcon />}
            >
              Assign & Start
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserSupportPage;

