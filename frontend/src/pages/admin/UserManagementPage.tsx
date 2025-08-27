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
  FormControlLabel,
  Switch,
} from '@mui/material';
import {
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';

import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import SkeletonLoader from '../../components/common/SkeletonLoader';
import adminService from '../../services/api/adminService';

interface User {
  user_id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_staff: boolean;
  role?: string;
  date_joined: string;
  last_login: string;
  total_appointments: number;
  total_resumes: number;
}

const UserManagementPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [roleFilter, setRoleFilter] = useState('all');
  const [staffFilter, setStaffFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState<'create' | 'edit' | 'delete' | 'block'>('edit');
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'student',
    is_staff: false
  });
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchUsers();
  }, [page, searchTerm, statusFilter]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await adminService.getUsers();
      setUsers(response);
      setTotalPages(1);
    } catch (err) {
      setError('Failed to load users');
      console.error('Error fetching users:', err);
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

  const handleRoleFilterChange = (event: any) => {
    setRoleFilter(event.target.value);
    setPage(1);
  };

  const handleStaffFilterChange = (event: any) => {
    setStaffFilter(event.target.value);
    setPage(1);
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const handleUserAction = (user: User, action: 'edit' | 'delete' | 'block') => {
    setSelectedUser(user);
    setDialogType(action);
    
    if (action === 'edit') {
      setFormData({
        username: user.username,
        email: user.email,
        password: '',
        role: user.role || 'student',
        is_staff: user.is_staff
      });
    }
    
    setDialogOpen(true);
  };

  const handleCreateUser = (role: 'student' | 'mentor' | 'staff' | 'admin') => {
    setSelectedUser(null);
    setDialogType('create');
    
    // Set role and staff status based on user type
    const isStaff = role === 'staff' || role === 'admin';
    const actualRole = role === 'staff' ? 'student' : role; // Staff users have student role but staff permissions
    
    setFormData({
      username: '',
      email: '',
      password: '',
      role: actualRole,
      is_staff: isStaff
    });
    setDialogOpen(true);
  };

  const handleFormChange = (field: string, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    setSelectedUser(null);
  };

  const handleConfirmAction = async () => {
    try {
      switch (dialogType) {
        case 'create':
          await adminService.createUser({
            username: formData.username,
            email: formData.email,
            password: formData.password,
            role: formData.role
          });
          setSuccess('User created successfully');
          break;
        case 'edit':
          if (!selectedUser) return;
          await adminService.updateUser(selectedUser.user_id, {
            username: formData.username,
            email: formData.email,
            role: formData.role,
            is_staff: formData.is_staff
          });
          setSuccess('User updated successfully');
          break;
        case 'delete':
          if (!selectedUser) return;
          await adminService.deleteUser(selectedUser.user_id);
          setSuccess('User deleted successfully');
          break;
        case 'block':
          if (!selectedUser) return;
          const action = selectedUser.is_active ? 'deactivate' : 'activate';
          await adminService.updateUserStatus(selectedUser.user_id, action);
          setSuccess(`User ${action}d successfully`);
          break;
      }
      handleDialogClose();
      fetchUsers(); // Refresh the list
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to perform action');
      console.error('Error performing action:', err);
    }
  };



  if (loading && users.length === 0) {
    return <LoadingSpinner message="Loading users..." />;
  }

  return (
    <>
      <PageHeader
        title="User Management"
        breadcrumbs={[
          { label: 'Admin', path: '/admin' },
          { label: 'Users', path: '/admin/users' },
        ]}
      />

      <Container maxWidth="xl">
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
              <TextField
                placeholder="Search users..."
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
                  <MenuItem value="all">All Users</MenuItem>
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                </Select>
              </FormControl>
              <FormControl sx={{ minWidth: 150 }}>
                <InputLabel>Role</InputLabel>
                <Select
                  value={roleFilter}
                  label="Role"
                  onChange={handleRoleFilterChange}
                >
                  <MenuItem value="all">All Roles</MenuItem>
                  <MenuItem value="student">Student</MenuItem>
                  <MenuItem value="mentor">Mentor</MenuItem>
                  <MenuItem value="admin">Admin</MenuItem>
                </Select>
              </FormControl>
              <FormControl sx={{ minWidth: 150 }}>
                <InputLabel>Staff Status</InputLabel>
                <Select
                  value={staffFilter}
                  label="Staff Status"
                  onChange={handleStaffFilterChange}
                >
                  <MenuItem value="all">All Users</MenuItem>
                  <MenuItem value="staff">Staff Only</MenuItem>
                  <MenuItem value="non-staff">Non-Staff Only</MenuItem>
                </Select>
              </FormControl>
              <Button
                variant="contained"
                startIcon={<FilterIcon />}
                onClick={() => {/* TODO: Implement advanced filters */}}
              >
                Advanced Filters
              </Button>
              <Box sx={{ display: 'flex', gap: 1, ml: 'auto' }}>
                <Button
                  variant="outlined"
                  color="primary"
                  onClick={() => handleCreateUser('student')}
                  size="small"
                >
                  Add Student
                </Button>
                <Button
                  variant="outlined"
                  color="primary"
                  onClick={() => handleCreateUser('mentor')}
                  size="small"
                >
                  Add Mentor
                </Button>
                <Button
                  variant="outlined"
                  color="secondary"
                  onClick={() => handleCreateUser('staff')}
                  size="small"
                >
                  Add Staff
                </Button>
                <Button
                  variant="contained"
                  color="error"
                  onClick={() => handleCreateUser('admin')}
                  size="small"
                >
                  Add Admin
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Users ({users.length})</Typography>
            </Box>

            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>User</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Role</TableCell>
                    <TableCell>Joined</TableCell>
                    <TableCell>Last Login</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={7}>
                        <SkeletonLoader type="table" count={3} />
                      </TableCell>
                    </TableRow>
                  ) : (
                    users.map((user) => (
                      <TableRow key={user.user_id} hover>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Avatar sx={{ mr: 2, width: 32, height: 32 }}>
                              {user.username.charAt(0).toUpperCase()}
                            </Avatar>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {user.username}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                @{user.username}
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>
                          <Chip 
                            label={user.is_active ? "Active" : "Inactive"} 
                            color={user.is_active ? "success" : "error"} 
                            size="small" 
                          />
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Chip 
                              label={user.role || 'student'} 
                              color={
                                user.role === 'admin' ? 'error' : 
                                user.role === 'mentor' ? 'primary' : 
                                'default'
                              } 
                              size="small" 
                            />
                            {user.is_staff && (
                              <Chip 
                                label="Staff" 
                                color="secondary" 
                                size="small" 
                              />
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          {new Date(user.date_joined).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          {new Date(user.last_login).toLocaleDateString()}
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={() => handleUserAction(user, 'edit')}
                            color="primary"
                          >
                            <EditIcon />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleUserAction(user, 'block')}
                            color={user.is_active ? 'warning' : 'success'}
                          >
                            {user.is_active ? <BlockIcon /> : <CheckCircleIcon />}
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleUserAction(user, 'delete')}
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

      {/* User Management Dialog */}
      <Dialog open={dialogOpen} onClose={handleDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dialogType === 'create' && `Create New ${formData.role === 'admin' ? 'Admin' : formData.role === 'mentor' ? 'Mentor' : formData.is_staff ? 'Staff' : 'Student'}`}
          {dialogType === 'edit' && 'Edit User'}
          {dialogType === 'delete' && 'Delete User'}
          {dialogType === 'block' && (selectedUser?.is_active ? 'Block User' : 'Unblock User')}
        </DialogTitle>
        <DialogContent>
          {(dialogType === 'create' || dialogType === 'edit') ? (
            <Box sx={{ pt: 1 }}>
              <TextField
                fullWidth
                label="Username"
                value={formData.username}
                onChange={(e) => handleFormChange('username', e.target.value)}
                margin="normal"
                required
              />
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => handleFormChange('email', e.target.value)}
                margin="normal"
                required
              />
              {dialogType === 'create' && (
                <TextField
                  fullWidth
                  label="Password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => handleFormChange('password', e.target.value)}
                  margin="normal"
                  required
                />
              )}
                              {dialogType === 'edit' && (
                  <>
                    <FormControl fullWidth margin="normal">
                      <InputLabel>Role</InputLabel>
                      <Select
                        value={formData.role}
                        label="Role"
                        onChange={(e) => handleFormChange('role', e.target.value)}
                      >
                        <MenuItem value="student">Student</MenuItem>
                        <MenuItem value="mentor">Mentor</MenuItem>
                        <MenuItem value="admin">Admin</MenuItem>
                      </Select>
                    </FormControl>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={formData.is_staff}
                          onChange={(e) => handleFormChange('is_staff', e.target.checked)}
                        />
                      }
                      label="Staff Member (Additional permissions)"
                      sx={{ mt: 1 }}
                    />
                  </>
                )}
                {dialogType === 'create' && (
                  <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Creating: <strong>{formData.role === 'admin' ? 'Admin' : formData.role === 'mentor' ? 'Mentor' : formData.is_staff ? 'Staff' : 'Student'}</strong>
                      {formData.is_staff && ' (with staff permissions)'}
                    </Typography>
                  </Box>
                )}
              
            </Box>
          ) : (
            <Typography>
              {dialogType === 'delete' && `Are you sure you want to delete ${selectedUser?.username}? This action cannot be undone.`}
              {dialogType === 'block' && selectedUser?.is_active 
                ? `Are you sure you want to block ${selectedUser?.username}?`
                : `Are you sure you want to unblock ${selectedUser?.username}?`
              }
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>Cancel</Button>
          <Button
            onClick={handleConfirmAction}
            color={dialogType === 'delete' ? 'error' : 'primary'}
            variant="contained"
          >
            {dialogType === 'create' && 'Create'}
            {dialogType === 'edit' && 'Update'}
            {dialogType === 'delete' && 'Delete'}
            {dialogType === 'block' && (selectedUser?.is_active ? 'Block' : 'Unblock')}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default UserManagementPage; 