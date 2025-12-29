import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  IconButton,
  InputBase,
} from '@mui/material';
import {
  Dashboard,
  Assessment,
  TrendingUp as Insights,
  People,
  Person,
  Settings,
  Logout,
  Search as SearchIcon,
  AdminPanelSettings,
  Badge as StaffIcon,
  Work as MentorIcon,
  School as StudentIcon,
  SwapHoriz as SwapIcon,
} from '@mui/icons-material';
import { RootState } from '../../store';
import { logout } from '../../store/slices/authSlice';
import { useRole } from '../../contexts/RoleContext';
import NotificationBell from '../common/NotificationBell';
import ViewingAsChip from '../common/ViewingAsChip';

const DashboardHeader: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);
  const { setOverrideRole, resetOverrideRole, isSuperAdmin } = useRole();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    dispatch(logout());
    resetOverrideRole();
    handleProfileMenuClose();
    navigate('/');
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    handleProfileMenuClose();
  };

  const getUserInitials = () => {
    if (user?.first_name && user?.last_name) {
      const first = user.first_name?.[0] || '';
      const last = user.last_name?.[0] || '';
      if (first && last) {
        return `${first}${last}`.toUpperCase();
      }
    }
    if (user?.username && user.username.length > 0) {
      return user.username[0].toUpperCase();
    }
    return 'U';
  };

  // Role switching functions (superadmin only)
  const switchRole = (targetRole: string) => {
    setOverrideRole(targetRole);
    handleProfileMenuClose();
    const dashboardPaths: Record<string, string> = {
      student: '/student',
      mentor: '/mentor',
      staff: '/staff',
      admin: '/admin',
    };
    const targetPath = dashboardPaths[targetRole] || '/';
    navigate(targetPath);
  };

  const resetRole = () => {
    resetOverrideRole();
    handleProfileMenuClose();
    navigate('/superadmin');
  };

  return (
    <AppBar
      position="sticky"
      elevation={1}
      sx={{
        bgcolor: 'white',
        color: 'text.primary',
        borderBottom: '1px solid',
        borderColor: 'divider',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar sx={{ minHeight: '64px !important', px: { xs: 2, md: 3 } }}>
        {/* Left: Logo */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer',
            mr: 3,
          }}
          onClick={() => navigate('/')}
        >
          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{
              fontWeight: 700,
              fontSize: '1.25rem',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            CareerBridge
          </Typography>
        </Box>

        {/* Center: Search Bar (optional) */}
        <Box
          sx={{
            position: 'relative',
            borderRadius: 2,
            bgcolor: 'grey.100',
            width: { xs: '100%', sm: '400px', md: '500px' },
            mr: 3,
            '&:hover': {
              bgcolor: 'grey.200',
            },
            display: { xs: 'none', md: 'block' },
          }}
        >
          <Box
            sx={{
              padding: '0 16px',
              height: '100%',
              position: 'absolute',
              pointerEvents: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <SearchIcon sx={{ color: 'text.secondary' }} />
          </Box>
          <InputBase
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            sx={{
              color: 'text.primary',
              width: '100%',
              pl: '48px',
              pr: '16px',
              py: '8px',
              '& .MuiInputBase-input': {
                fontSize: '0.938rem',
              },
            }}
          />
        </Box>

        {/* Spacer */}
        <Box sx={{ flexGrow: 1 }} />

        {/* Right: Notifications & Profile */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Notifications */}
          <NotificationBell />

          {/* Avatar and Viewing As Chip */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton
              onClick={handleProfileMenuOpen}
              sx={{
                p: 0,
                '&:hover': { opacity: 0.8 },
              }}
            >
              <Avatar
                src={user?.avatar}
                sx={{
                  width: 36,
                  height: 36,
                  bgcolor: 'primary.main',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  cursor: 'pointer',
                }}
              >
                {getUserInitials()}
              </Avatar>
            </IconButton>
            <ViewingAsChip />
          </Box>

          {/* Profile Menu */}
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleProfileMenuClose}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            sx={{
              mt: 1.5,
              '& .MuiPaper-root': {
                minWidth: 220,
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              },
            }}
          >
            {/* SuperAdmin Role Switching Section */}
            {isSuperAdmin && (
              <>
                <MenuItem disabled sx={{ opacity: 1, fontWeight: 600 }}>
                  <SwapIcon sx={{ mr: 2, fontSize: 20 }} />
                  Switch Role
                </MenuItem>
                <MenuItem onClick={() => switchRole('student')}>
                  <StudentIcon sx={{ mr: 2, fontSize: 20 }} />
                  View as Student
                </MenuItem>
                <MenuItem onClick={() => switchRole('mentor')}>
                  <MentorIcon sx={{ mr: 2, fontSize: 20 }} />
                  View as Mentor
                </MenuItem>
                <MenuItem onClick={() => switchRole('staff')}>
                  <StaffIcon sx={{ mr: 2, fontSize: 20 }} />
                  View as Staff
                </MenuItem>
                <MenuItem onClick={() => switchRole('admin')}>
                  <AdminPanelSettings sx={{ mr: 2, fontSize: 20 }} />
                  View as Admin
                </MenuItem>
                <MenuItem onClick={resetRole}>
                  <SwapIcon sx={{ mr: 2, fontSize: 20 }} />
                  Reset to Superadmin
                </MenuItem>
                <Divider />
              </>
            )}

            <MenuItem onClick={() => handleNavigation('/dashboard')}>
              <Dashboard sx={{ mr: 2, fontSize: 20 }} />
              Dashboard
            </MenuItem>
            <MenuItem onClick={() => handleNavigation('/dashboard/assessment')}>
              <Assessment sx={{ mr: 2, fontSize: 20 }} />
              My Assessments
            </MenuItem>
            <MenuItem onClick={() => handleNavigation('/dashboard/intelligence')}>
              <Insights sx={{ mr: 2, fontSize: 20 }} />
              My Insights
            </MenuItem>
            <MenuItem onClick={() => handleNavigation('/mentors')}>
              <People sx={{ mr: 2, fontSize: 20 }} />
              My Mentors
            </MenuItem>
            <Divider />
            <MenuItem onClick={() => handleNavigation('/profile')}>
              <Person sx={{ mr: 2, fontSize: 20 }} />
              Profile
            </MenuItem>
            <MenuItem onClick={() => handleNavigation('/settings')}>
              <Settings sx={{ mr: 2, fontSize: 20 }} />
              Settings
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <Logout sx={{ mr: 2, fontSize: 20 }} />
              Logout
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default DashboardHeader;
