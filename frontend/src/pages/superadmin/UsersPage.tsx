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
  IconButton,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { useRole } from '../../contexts/RoleContext';
import adminService from '../../services/api/adminService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import { createApiError, handleApiError } from '../../services/utils/errorHandler';
import type { ApiError } from '../../services/utils/errorHandler';

interface User {
  user_id: number;
  username: string;
  email: string;
  role?: string;
  is_active: boolean;
  is_staff: boolean;
  date_joined: string;
  last_login: string | null;
  total_appointments: number;
  total_resumes: number;
}

const UsersPage: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const { isSuperAdmin } = useRole();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    role: '',
    is_active: true,
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('>>> DEBUG: SuperAdmin UsersPage fetching users...');
      const response = await adminService.getUsers();
      console.log('>>> DEBUG: SuperAdmin UsersPage response:', response);
      
      // Handle different response formats
      let usersData: User[] = [];
      if (Array.isArray(response)) {
        usersData = response;
      } else if (response && typeof response === 'object' && Array.isArray(response.results)) {
        usersData = response.results;
      } else if (response && typeof response === 'object' && Array.isArray(response.data)) {
        usersData = response.data;
      } else {
        console.error('>>> DEBUG: Unexpected response format:', response);
        setError(createApiError('Unexpected response format from backend', 'VALIDATION_ERROR'));
        usersData = [];
      }
      
      // Normalize user data
      const normalizedUsers: User[] = usersData.map((user: any) => ({
        user_id: user.user_id || user.id,
        username: user.username || '',
        email: user.email || '',
        role: user.role || 'student',
        is_active: user.is_active !== undefined ? user.is_active : true,
        is_staff: user.is_staff !== undefined ? user.is_staff : false,
        date_joined: user.date_joined || new Date().toISOString(),
        last_login: user.last_login || null,
        total_appointments: user.total_appointments || 0,
        total_resumes: user.total_resumes || 0,
      }));
      
      console.log('>>> DEBUG: SuperAdmin UsersPage normalized users:', normalizedUsers.length);
      setUsers(normalizedUsers);
    } catch (err: any) {
      console.error('>>> DEBUG: SuperAdmin UsersPage error:', err);
      setError(handleApiError(err));
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (user: any) => {
    setSelectedUser(user);
    setFormData({
      username: user.username,
      email: user.email,
      role: user.role,
      is_active: user.is_active,
    });
    setEditDialogOpen(true);
  };

  const handleSave = async () => {
    if (!selectedUser) return;
    try {
      await adminService.updateUser(selectedUser.user_id, {
        username: formData.username,
        email: formData.email,
        role: formData.role,
        is_active: formData.is_active,
      });
      setEditDialogOpen(false);
      fetchUsers(); // Refresh user list
    } catch (err: any) {
      console.error('Failed to update user:', err);
      setError(handleApiError(err));
    }
  };

  const handleDelete = async (userId: number) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await adminService.deleteUser(userId);
        fetchUsers(); // Refresh user list
      } catch (err: any) {
        console.error('Failed to delete user:', err);
        setError(handleApiError(err));
      }
    }
  };

  const handleToggleActive = async (userId: number) => {
    const user = users.find(u => u.user_id === userId);
    if (!user) return;
    
    try {
      const action = user.is_active ? 'deactivate' : 'activate';
      await adminService.updateUserStatus(userId, action);
      fetchUsers(); // Refresh user list
    } catch (err: any) {
      console.error('Failed to toggle user status:', err);
      setError(handleApiError(err));
    }
  };

  if (!isSuperAdmin) {
    return null;
  }

  if (loading) {
    return <LoadingSpinner message="Loading users..." />;
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
          User Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage all users, roles, and permissions
        </Typography>
      </Box>

      {error && (
        <ErrorAlert error={error} overrideMessage="Failed to load users." />
      )}

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Username</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Role</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Joined</TableCell>
                <TableCell>Last Login</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No users found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                users.map((user) => (
                  <TableRow key={user.user_id}>
                    <TableCell>{user.user_id}</TableCell>
                    <TableCell>{user.username}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Chip 
                        label={user.role || 'student'} 
                        size="small" 
                        color={
                          user.role === 'superadmin' ? 'error' :
                          user.role === 'admin' ? 'warning' :
                          user.role === 'mentor' ? 'primary' :
                          'default'
                        } 
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={user.is_active ? 'Active' : 'Inactive'}
                        size="small"
                        color={user.is_active ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      {new Date(user.date_joined).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                    </TableCell>
                    <TableCell>
                      <IconButton size="small" onClick={() => handleEdit(user)}>
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleToggleActive(user.user_id)}
                        color={user.is_active ? 'warning' : 'success'}
                      >
                        {user.is_active ? <BlockIcon /> : <CheckCircleIcon />}
                      </IconButton>
                      <IconButton size="small" onClick={() => handleDelete(user.user_id)} color="error">
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

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit User</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Username"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            select
            label="Role"
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            margin="normal"
          >
            <MenuItem value="student">Student</MenuItem>
            <MenuItem value="mentor">Mentor</MenuItem>
            <MenuItem value="staff">Staff</MenuItem>
            <MenuItem value="admin">Admin</MenuItem>
            <MenuItem value="superadmin">Superadmin</MenuItem>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSave} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default UsersPage;
