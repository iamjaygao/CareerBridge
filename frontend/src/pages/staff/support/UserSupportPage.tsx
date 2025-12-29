import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
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
  Autocomplete,
  CircularProgress,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Assignment as AssignIcon,
  CheckCircle as ResolveIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../../components/common/LoadingSpinner';
import adminService from '../../../services/api/adminService';
import { useNotification } from '../../../components/common/NotificationProvider';
import { useSelector } from 'react-redux';
import { RootState } from '../../../store';

interface SupportTicket {
  id: number;
  user: {
    name: string;
    email: string;
  };
  issue: string;
  description: string;
  staff_notes?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  assigned_staff?: string;
  created_at: string;
}

interface UserOption {
  id: number;
  name: string;
  email: string;
  role?: string;
}

const UserSupportPage: React.FC = () => {
  const { showSuccess, showError } = useNotification();
  const currentUser = useSelector((state: RootState) => state.auth.user);
  const [loading, setLoading] = useState(true);
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [staffNotes, setStaffNotes] = useState('');
  const [statusFilter, setStatusFilter] = useState<'open' | 'in_progress' | null>(null);
  const [priorityFilter, setPriorityFilter] = useState<'urgent' | null>(null);
  const [userOptions, setUserOptions] = useState<UserOption[]>([]);
  const [userQuery, setUserQuery] = useState('');
  const [userLoading, setUserLoading] = useState(false);
  const location = useLocation();
  const [createForm, setCreateForm] = useState({
    userId: '',
    issue: '',
    description: '',
    priority: 'medium' as SupportTicket['priority'],
  });

  useEffect(() => {
    const fetchTickets = async () => {
      try {
        const data = await adminService.getSupportTickets();
        const list = Array.isArray(data) ? data : (data?.results || []);
        const mapped = list.map((ticket: any) => ({
          id: ticket.id,
          user: {
            name: ticket.user_name || ticket.user?.username || 'User',
            email: ticket.user_email || ticket.user?.email || '',
          },
          issue: ticket.issue,
          description: ticket.description || '',
          staff_notes: ticket.staff_notes || '',
          priority: ticket.priority,
          status: ticket.status,
          assigned_staff: ticket.assigned_staff_name || (ticket.assigned_staff ? String(ticket.assigned_staff) : ''),
          created_at: ticket.created_at,
        }));
        setTickets(mapped);
      } catch {
        showError('Failed to load support tickets.');
        setTickets([]);
      } finally {
        setLoading(false);
      }
    };

    fetchTickets();
  }, [showError]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const statusParam = params.get('status');
    const priorityParam = params.get('priority');

    if (statusParam === 'open' || statusParam === 'in_progress') {
      setStatusFilter(statusParam);
    } else {
      setStatusFilter(null);
    }

    if (priorityParam === 'urgent') {
      setPriorityFilter('urgent');
    } else {
      setPriorityFilter(null);
    }
  }, [location.search]);

  useEffect(() => {
    if (!createDialogOpen) {
      setUserOptions([]);
      setUserQuery('');
      setUserLoading(false);
      return;
    }

    if (!userQuery.trim() || userQuery.trim().length < 2) {
      setUserOptions([]);
      return;
    }

    let isActive = true;
    const handle = setTimeout(async () => {
      try {
        setUserLoading(true);
        const data = await adminService.searchUsers({ search: userQuery.trim(), limit: 10 });
        if (!isActive) return;
        const list = Array.isArray(data) ? data : (data?.results || []);
        const mapped = list.map((user: any) => ({
          id: user.id ?? user.user_id,
          name: user.name || user.username || user.email || 'User',
          email: user.email || '',
          role: user.role,
        }));
        setUserOptions(mapped);
      } catch {
        if (isActive) {
          setUserOptions([]);
        }
      } finally {
        if (isActive) {
          setUserLoading(false);
        }
      }
    }, 300);

    return () => {
      isActive = false;
      clearTimeout(handle);
    };
  }, [createDialogOpen, userQuery]);

  const handleView = (ticket: SupportTicket) => {
    setSelectedTicket(ticket);
    setStaffNotes(ticket.staff_notes || '');
    setDialogOpen(true);
  };

  const handleAssign = async () => {
    if (!selectedTicket) return;
    if (!currentUser?.id) {
      showError('Unable to assign ticket without a staff user.');
      return;
    }
    try {
      await adminService.updateSupportTicket(selectedTicket.id, {
        assigned_staff: currentUser.id,
        status: 'in_progress',
      });
      setTickets(tickets.map(t =>
        t.id === selectedTicket.id
          ? {
              ...t,
              assigned_staff: currentUser.username || 'Staff',
              status: 'in_progress' as const,
            }
          : t
      ));
      showSuccess('Ticket assigned.');
      setDialogOpen(false);
    } catch {
      showError('Failed to assign ticket.');
    }
  };

  const handleResolve = async (id: number) => {
    try {
      await adminService.updateSupportTicket(id, { status: 'resolved' });
      setTickets(tickets.map(t =>
        t.id === id
          ? { ...t, status: 'resolved' as const }
          : t
      ));
      showSuccess('Ticket resolved.');
    } catch {
      showError('Failed to resolve ticket.');
    }
  };

  const handleSaveNotes = async () => {
    if (!selectedTicket) return;
    try {
      await adminService.updateSupportTicket(selectedTicket.id, { staff_notes: staffNotes });
      setTickets(tickets.map(t =>
        t.id === selectedTicket.id
          ? { ...t, staff_notes: staffNotes }
          : t
      ));
      showSuccess('Notes updated.');
    } catch {
      showError('Failed to update notes.');
    }
  };

  const handleCreateTicket = async () => {
    if (!createForm.userId || !createForm.issue) {
      showError('User ID and issue are required.');
      return;
    }
    try {
      const created = await adminService.createSupportTicket({
        user: Number(createForm.userId),
        issue: createForm.issue,
        description: createForm.description,
        priority: createForm.priority,
        status: 'open',
      });
      const newTicket: SupportTicket = {
        id: created.id,
        user: {
          name: created.user_name || 'User',
          email: created.user_email || '',
        },
        issue: created.issue || createForm.issue,
        description: created.description || createForm.description,
        staff_notes: created.staff_notes || '',
        priority: created.priority || createForm.priority,
        status: created.status || 'open',
        assigned_staff: created.assigned_staff_name || '',
        created_at: created.created_at || new Date().toISOString(),
      };
      setTickets([newTicket, ...tickets]);
      setCreateDialogOpen(false);
      setCreateForm({ userId: '', issue: '', description: '', priority: 'medium' });
      showSuccess('Support ticket created.');
    } catch {
      showError('Failed to create support ticket.');
    }
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

  const filteredTickets = tickets.filter((ticket) => {
    if (statusFilter && ticket.status !== statusFilter) return false;
    if (priorityFilter && ticket.priority !== priorityFilter) return false;
    return true;
  });

  if (loading) {
    return <LoadingSpinner message="Loading support tickets..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            User Support
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage user support tickets and issues
          </Typography>
        </Box>
        <Button variant="contained" onClick={() => setCreateDialogOpen(true)}>
          Create Ticket
        </Button>
      </Box>

      {/* Stats Cards */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <Card
          sx={{ flex: 1, minWidth: 150, cursor: 'pointer', border: statusFilter === 'open' ? '1px solid' : 'none', borderColor: 'warning.main' }}
          onClick={() => {
            setStatusFilter(statusFilter === 'open' ? null : 'open');
            setPriorityFilter(null);
          }}
        >
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {tickets.filter(t => t.status === 'open').length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Open Tickets
            </Typography>
          </CardContent>
        </Card>
        <Card
          sx={{ flex: 1, minWidth: 150, cursor: 'pointer', border: statusFilter === 'in_progress' ? '1px solid' : 'none', borderColor: 'info.main' }}
          onClick={() => {
            setStatusFilter(statusFilter === 'in_progress' ? null : 'in_progress');
            setPriorityFilter(null);
          }}
        >
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {tickets.filter(t => t.status === 'in_progress').length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              In Progress
            </Typography>
          </CardContent>
        </Card>
        <Card
          sx={{ flex: 1, minWidth: 150, cursor: 'pointer', border: priorityFilter === 'urgent' ? '1px solid' : 'none', borderColor: 'error.main' }}
          onClick={() => {
            setPriorityFilter(priorityFilter === 'urgent' ? null : 'urgent');
            setStatusFilter(null);
          }}
        >
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
      {(statusFilter || priorityFilter) && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2, flexWrap: 'wrap' }}>
          <Typography variant="body2" color="text.secondary">
            Filtered by
          </Typography>
          {statusFilter && (
            <Chip label={`Status: ${statusFilter.replace('_', ' ')}`} size="small" />
          )}
          {priorityFilter && (
            <Chip label={`Priority: ${priorityFilter}`} size="small" color="error" />
          )}
          <Button size="small" onClick={() => { setStatusFilter(null); setPriorityFilter(null); }}>
            Clear
          </Button>
        </Box>
      )}

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
                {filteredTickets.map((ticket) => (
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
                <Typography variant="body2" color="text.secondary">Internal Notes</Typography>
                <TextField
                  fullWidth
                  value={staffNotes}
                  onChange={(e) => setStaffNotes(e.target.value)}
                  multiline
                  minRows={3}
                  sx={{ mt: 1 }}
                />
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
                <TextField
                  fullWidth
                  label="Assigned Staff"
                  value={currentUser?.username || 'Current staff'}
                  disabled
                  sx={{ mt: 2 }}
                />
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
          <Button variant="outlined" onClick={handleSaveNotes}>
            Save Notes
          </Button>
          {!selectedTicket?.assigned_staff && (
            <Button
              variant="contained"
              onClick={handleAssign}
              startIcon={<AssignIcon />}
            >
              Assign to Me
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Create Ticket Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Support Ticket</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'grid', gap: 2 }}>
            <Autocomplete
              options={userOptions}
              loading={userLoading}
              value={userOptions.find((option) => String(option.id) === createForm.userId) || null}
              onChange={(_, value) => setCreateForm({ ...createForm, userId: value ? String(value.id) : '' })}
              inputValue={userQuery}
              onInputChange={(_, value) => setUserQuery(value)}
              getOptionLabel={(option) => `${option.name}${option.email ? ` (${option.email})` : ''}`}
              noOptionsText={userQuery.trim().length < 2 ? 'Type at least 2 characters to search' : 'No users found'}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="User"
                  required
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {userLoading ? <CircularProgress color="inherit" size={18} /> : null}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  }}
                />
              )}
              renderOption={(props, option) => (
                <Box component="li" {...props}>
                  <Box>
                    <Typography variant="body2" fontWeight="medium">
                      {option.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {option.email || `ID: ${option.id}`}
                    </Typography>
                  </Box>
                </Box>
              )}
            />
            <TextField
              label="Issue"
              value={createForm.issue}
              onChange={(e) => setCreateForm({ ...createForm, issue: e.target.value })}
              required
            />
            <TextField
              label="Description"
              value={createForm.description}
              onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              multiline
              minRows={3}
            />
            <TextField
              select
              label="Priority"
              value={createForm.priority}
              onChange={(e) => setCreateForm({ ...createForm, priority: e.target.value as SupportTicket['priority'] })}
            >
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="urgent">Urgent</MenuItem>
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateTicket}>
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserSupportPage;
