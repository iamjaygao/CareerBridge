/**
 * Kernel World Layout (Phase-A World Isolation)
 * 
 * Purpose:
 * - Pure Kernel Control Plane layout
 * - ZERO business world dependencies
 * - No legacy runtime pollution
 * 
 * Prohibited:
 * - NotificationBell (triggers /api/v1/notifications/* - AI_BUS)
 * - Search components (triggers /api/v1/search/* - SEARCH_BUS)
 * - Chat / Socket / Signal-delivery hooks (triggers frozen APIs)
 * - Unread-count / polling hooks (triggers business APIs)
 * 
 * Allowed:
 * - Kernel-only TopBar (no notifications)
 * - Kernel-only SideBar (3 menu items only)
 * - React Router Outlet
 */

import React, { useState } from 'react';
import { Box, AppBar, Toolbar, IconButton, Typography, Avatar, Menu, MenuItem, Divider } from '@mui/material';
import { Outlet, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { Menu as MenuIcon, Person, Settings, Logout } from '@mui/icons-material';
import { RootState } from '../store';
import { logout } from '../store/slices/authSlice';
import KernelWorldSidebar from './KernelWorldSidebar';

const KernelWorldLayout: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector((state: RootState) => state.auth);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

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
    return 'SA';
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: '#F8FAFC' }}>
      {/* Kernel World Sidebar - Pure Kernel Menu Only */}
      <KernelWorldSidebar
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      {/* Main content area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - 260px)` },
          minWidth: 0,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Kernel World TopBar - No Notifications, No Search */}
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
              onClick={handleDrawerToggle}
              sx={{
                mr: 2,
                display: { md: 'none' },
                color: 'text.primary',
              }}
            >
              <MenuIcon />
            </IconButton>

            {/* Kernel World Title */}
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                color: 'text.primary',
                fontSize: '1.125rem',
              }}
            >
              GateAI OS Kernel Control Plane
            </Typography>

            {/* Spacer */}
            <Box sx={{ flexGrow: 1 }} />

            {/* Right side - Avatar only (NO NotificationBell) */}
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
              <MenuItem onClick={() => { navigate('/profile'); handleProfileMenuClose(); }}>
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
          </Toolbar>
        </AppBar>

        {/* Page content */}
        <Box
          sx={{
            flexGrow: 1,
            p: { xs: 2, sm: 3, md: 4 },
            bgcolor: '#F8FAFC',
          }}
        >
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
};

export default KernelWorldLayout;
