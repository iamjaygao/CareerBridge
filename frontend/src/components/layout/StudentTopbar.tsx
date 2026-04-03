import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Box,
  InputBase,
  Avatar,
  Menu,
  MenuItem,
  Divider,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Search as SearchIcon,
  Person,
  Settings,
  Logout,
  Home,
} from '@mui/icons-material';
import { RootState } from '../../store';
import { logout } from '../../store/slices/authSlice';
import NotificationBell from '../common/NotificationBell';

interface StudentTopbarProps {
  onMenuClick: () => void;
}

const StudentTopbar: React.FC<StudentTopbarProps> = ({ onMenuClick }) => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector((state: RootState) => state.auth);
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
    handleProfileMenuClose();
    navigate('/');
  };

  const getUserInitials = () => {
    if (user?.first_name && user?.last_name) {
      const first = (user.first_name as string)?.[0] || '';
      const last = (user.last_name as string)?.[0] || '';
      if (first && last) {
        return `${first}${last}`.toUpperCase();
      }
    }
    if (user?.username && user.username.length > 0) {
      return user.username[0].toUpperCase();
    }
    return 'S';
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
      }}
    >
      <Toolbar sx={{ minHeight: '64px !important', px: { xs: 2, md: 3 } }}>
        {/* Mobile menu button */}
        <IconButton
          edge="start"
          onClick={onMenuClick}
          sx={{
            mr: 2,
            display: { md: 'none' },
            color: 'text.primary',
          }}
        >
          <MenuIcon />
        </IconButton>

        {/* Title */}
        <Typography
          variant="h6"
          noWrap
          component="div"
          sx={{
            display: { xs: 'none', sm: 'block' },
            mr: 3,
            fontWeight: 600,
            color: 'text.primary',
          }}
        >
          Student Portal
        </Typography>

        {/* Search bar */}
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
            placeholder="Search mentors, resources, jobs..."
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

        {/* Right side actions */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Notifications */}
          <NotificationBell />

          {/* Home link */}
          <IconButton
            onClick={() => navigate('/?from=portal')}
            sx={{
              color: 'text.primary',
              '&:hover': { bgcolor: 'grey.100' },
            }}
            title="Go to homepage"
          >
            <Home />
          </IconButton>

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
        </Box>

          {/* Profile menu */}
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
                minWidth: 200,
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              },
            }}
          >
            <MenuItem onClick={() => { navigate('/student/profile'); handleProfileMenuClose(); }}>
              <Person sx={{ mr: 2, fontSize: 20 }} />
              Profile
            </MenuItem>
            <MenuItem onClick={() => { navigate('/settings'); handleProfileMenuClose(); }}>
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

export default StudentTopbar;
