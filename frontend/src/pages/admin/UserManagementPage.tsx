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
  FormControlLabel,
  Switch,
  Divider,
  Grid,
} from '@mui/material';
import {
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';

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
  const [actionLoading, setActionLoading] = useState(false);
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
  }, [page, searchTerm, statusFilter, roleFilter, staffFilter]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null); // Clear previous errors
      
      // Build filter parameters
      const params: any = {};
      if (searchTerm) params.search = searchTerm;
      if (statusFilter !== 'all') {
        params.is_active = statusFilter === 'active';
      }
      if (roleFilter !== 'all') {
        params.role = roleFilter;
      }
      // Staff status filter (is_staff flag) - separate from role filter
      // When roleFilter='staff', we only want role='staff' users (not admin)
      // So we should NOT apply staff status filter when roleFilter='staff' to avoid conflict
      // When staffFilter='staff': show users with is_staff=true OR role='admin' (admin is always staff)
      // When staffFilter='non-staff': show users with is_staff=false AND role!='admin'
      if (staffFilter !== 'all' && roleFilter !== 'staff') {
        // Only apply staff status filter if we're not filtering by role='staff'
        // This prevents showing admin when filtering by role='staff'
        if (staffFilter === 'staff') {
          params.is_staff = true;
        } else if (staffFilter === 'non-staff') {
          params.is_staff = false;
          params.exclude_admin = true;
        }
      }
      if (page > 1) params.page = page;
      
      console.log('>>> DEBUG: Fetching users with params:', params);
      const response = await adminService.getUsers(params);
      console.log('>>> DEBUG: Users API response (from adminService):', response);
      console.log('>>> DEBUG: Response type:', typeof response);
      console.log('>>> DEBUG: Response isArray:', Array.isArray(response));
      console.log('>>> DEBUG: Response keys:', response && typeof response === 'object' ? Object.keys(response) : 'N/A');
      
      // Handle different response formats
      // adminService.getUsers already returns response.data, so response is the actual data
      let usersData: any[] = [];
      let totalPagesCount = 1;
      
      console.log('>>> DEBUG: Processing response:', {
        type: typeof response,
        isArray: Array.isArray(response),
        keys: response && typeof response === 'object' ? Object.keys(response) : 'N/A',
        response: response
      });
      
      // Option A: Direct array response (most common case)
      if (Array.isArray(response)) {
        usersData = response;
        console.log('>>> DEBUG: Option A - Direct array response with', usersData.length, 'users');
      }
      // Option B: Paginated response: { count, next, previous, results: [...] }
      else if (response && typeof response === 'object' && Array.isArray(response.results)) {
        usersData = response.results;
        totalPagesCount = Math.ceil((response.count || usersData.length) / 10) || 1;
        console.log('>>> DEBUG: Option B - Paginated response:', {
          count: response.count,
          results: usersData.length,
          totalPages: totalPagesCount
        });
      }
      // Option C: Nested data response: { data: [...] }
      else if (response && typeof response === 'object' && Array.isArray(response.data)) {
        usersData = response.data;
        console.log('>>> DEBUG: Option C - Nested data response with', usersData.length, 'users');
      }
      // Option D: Double nested: { data: { results: [...] } }
      else if (response && typeof response === 'object' && response.data && Array.isArray(response.data.results)) {
        usersData = response.data.results;
        totalPagesCount = Math.ceil((response.data.count || usersData.length) / 10) || 1;
        console.log('>>> DEBUG: Option D - Double nested response with', usersData.length, 'users');
      }
      else {
        console.error('>>> DEBUG: UNEXPECTED RESPONSE FORMAT:', response);
        console.error('>>> DEBUG: Response structure:', JSON.stringify(response, null, 2));
        console.error('>>> DEBUG: Response type:', typeof response);
        console.error('>>> DEBUG: Response isArray:', Array.isArray(response));
        if (response && typeof response === 'object') {
          console.error('>>> DEBUG: Response keys:', Object.keys(response));
        }
        usersData = [];
        setError(`Unexpected response format from backend. Received: ${typeof response}. Check console for details.`);
      }
      
      // Validate user data structure
      const validUsers: User[] = [];
      usersData.forEach((user: any, index: number) => {
        const isValid = user && (user.user_id || user.id) && user.username && user.email;
        if (!isValid) {
          console.warn(`>>> DEBUG: Invalid user object at index ${index}:`, user);
        } else {
          // Normalize user object to ensure consistent structure
          validUsers.push({
            user_id: user.user_id || user.id,
            username: user.username,
            email: user.email,
            is_active: user.is_active !== undefined ? user.is_active : true,
            is_staff: user.is_staff !== undefined ? user.is_staff : false,
            role: user.role || 'student',
            date_joined: user.date_joined || new Date().toISOString(),
            last_login: user.last_login || null,
            total_appointments: user.total_appointments || 0,
            total_resumes: user.total_resumes || 0,
          });
        }
      });
      
      console.log('>>> DEBUG: Valid users count:', validUsers.length);
      console.log('>>> DEBUG: First valid user sample:', validUsers[0]);
      
      if (validUsers.length === 0 && usersData.length > 0) {
        console.error('>>> DEBUG: ALL USERS WERE INVALID! Raw usersData:', usersData);
        setError('Received invalid user data from backend. Check console for details.');
      }
      
      setUsers(validUsers);
      setTotalPages(totalPagesCount);
      console.log('>>> DEBUG: Set users state with', validUsers.length, 'valid users');
      
    } catch (err: any) {
      console.error('>>> DEBUG: Error fetching users:', err);
      const errorMessage = err?.response?.data?.detail 
        || err?.response?.data?.error 
        || err?.response?.data?.message
        || err?.message 
        || 'Failed to load users. Please check your connection and try again.';
      setError(`Failed to load users: ${errorMessage}`);
      setUsers([]); // Clear users on error
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
    // Filter will be applied automatically via useEffect
  };

  const handleRoleFilterChange = (event: any) => {
    setRoleFilter(event.target.value);
    setPage(1);
    // Filter will be applied automatically via useEffect
  };

  const handleStaffFilterChange = (event: any) => {
    setStaffFilter(event.target.value);
    setPage(1);
    // Filter will be applied automatically via useEffect
  };

  const handleApplyFilters = () => {
    setPage(1);
    fetchUsers();
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setRoleFilter('all');
    setStaffFilter('all');
    setPage(1);
    // Filters will be cleared and fetchUsers will be called via useEffect
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
    
    setFormData({
      username: '',
      email: '',
      password: '',
      role: role,
      is_staff: false // Staff is now a separate role
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
    setError(null); // Clear any errors when closing dialog
    setFormData({
      username: '',
      email: '',
      password: '',
      role: 'student',
      is_staff: false
    });
  };

  const handleConfirmAction = async () => {
    setError(null); // Clear previous errors
    setActionLoading(true);
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
      setDialogOpen(false); // Close dialog first
      setSelectedUser(null);
      setFormData({
        username: '',
        email: '',
        password: '',
        role: 'student',
        is_staff: false
      });
      fetchUsers(); // Refresh the list
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.error || err.response?.data?.message || 'Failed to perform action');
      console.error('Error performing action:', err);
      // Don't close dialog on error so user can see the error message
    } finally {
      setActionLoading(false);
    }
  };



  if (loading && users.length === 0) {
    return <LoadingSpinner message="Loading users..." />;
  }

  return (
    <>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          User Management
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Manage users, roles, and permissions
        </Typography>
      </Box>

      <Box>
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
            <Grid container spacing={2} alignItems="center">
              {/* Search and Filters Section */}
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
                  <TextField
                    placeholder="Search users..."
                    value={searchTerm}
                    onChange={handleSearch}
                    InputProps={{
                      startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                    }}
                    sx={{ minWidth: 280, flexGrow: 1, maxWidth: 350 }}
                    size="small"
                  />
                  <FormControl sx={{ minWidth: 140 }} size="small">
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
                  <FormControl sx={{ minWidth: 140 }} size="small">
                    <InputLabel>Role</InputLabel>
                    <Select
                      value={roleFilter}
                      label="Role"
                      onChange={handleRoleFilterChange}
                    >
                      <MenuItem value="all">All Roles</MenuItem>
                      <MenuItem value="student">Student</MenuItem>
                      <MenuItem value="mentor">Mentor</MenuItem>
                      <MenuItem value="staff">Staff</MenuItem>
                      <MenuItem value="admin">Admin</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl sx={{ minWidth: 140 }} size="small">
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
                </Box>
              </Grid>
              
              {/* Action Buttons Section */}
              <Grid item xs={12}>
                <Divider sx={{ my: 1 }} />
                <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                  {/* Filter Actions Group */}
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={handleApplyFilters}
                      disabled={loading}
                      startIcon={<FilterIcon />}
                      size="medium"
                    >
                      Apply Filters
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={handleClearFilters}
                      disabled={loading}
                      size="medium"
                    >
                      Clear Filters
                    </Button>
                  </Box>
                  
                  {/* Add User Actions Group */}
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mr: 0.5, fontWeight: 500 }}>
                      Add:
                    </Typography>
                    <Button
                      variant="outlined"
                      color="primary"
                      onClick={() => handleCreateUser('student')}
                      size="small"
                    >
                      Student
                    </Button>
                    <Button
                      variant="outlined"
                      color="primary"
                      onClick={() => handleCreateUser('mentor')}
                      size="small"
                    >
                      Mentor
                    </Button>
                    <Button
                      variant="outlined"
                      color="primary"
                      onClick={() => handleCreateUser('staff')}
                      size="small"
                    >
                      Staff
                    </Button>
                    <Button
                      variant="contained"
                      color="error"
                      onClick={() => handleCreateUser('admin')}
                      size="small"
                    >
                      Admin
                    </Button>
                  </Box>
                </Box>
              </Grid>
            </Grid>
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
                                user.role === 'staff' ? 'warning' :
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
      </Box>

      {/* User Management Dialog */}
      <Dialog open={dialogOpen} onClose={handleDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dialogType === 'create' && `Create New ${formData.role === 'admin' ? 'Admin' : formData.role === 'mentor' ? 'Mentor' : formData.role === 'staff' ? 'Staff' : 'Student'}`}
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
                        <MenuItem value="staff">Staff</MenuItem>
                        <MenuItem value="admin">Admin</MenuItem>
                      </Select>
                    </FormControl>
                    {/* Staff is now a separate role, so is_staff switch is only for legacy compatibility */}
                    {formData.role !== 'staff' && formData.role !== 'admin' && (
                      <FormControlLabel
                        control={
                          <Switch
                            checked={formData.is_staff}
                            onChange={(e) => handleFormChange('is_staff', e.target.checked)}
                          />
                        }
                        label="Staff Member (Additional permissions - legacy)"
                        sx={{ mt: 1 }}
                      />
                    )}
                  </>
                )}
                {dialogType === 'create' && (
                  <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Creating: <strong>{formData.role === 'admin' ? 'Admin' : formData.role === 'mentor' ? 'Mentor' : formData.role === 'staff' ? 'Staff' : 'Student'}</strong>
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
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose} disabled={actionLoading}>
            Cancel
          </Button>
          {error && (
            <Button onClick={() => setError(null)} color="warning" disabled={actionLoading}>
              Dismiss Error
            </Button>
          )}
          <Button
            onClick={handleConfirmAction}
            color={dialogType === 'delete' ? 'error' : 'primary'}
            variant="contained"
            disabled={actionLoading}
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