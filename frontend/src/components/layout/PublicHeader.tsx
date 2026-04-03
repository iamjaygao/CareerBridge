import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import {
  Box,
  AppBar,
  Toolbar,
  Button,
  Typography,
  Container,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  IconButton,
} from '@mui/material';
import {
  Dashboard,
  Person,
  Settings,
  Logout,
  Menu as MenuIcon,
} from '@mui/icons-material';
import { RootState } from '../../store';
import { logout } from '../../store/slices/authSlice';
import { getLandingPathByRole } from '../../utils/roleLanding';
import NotificationBell from '../common/NotificationBell';

const PublicHeader: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [mobileMenuAnchor, setMobileMenuAnchor] = useState<null | HTMLElement>(null);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleMobileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setMobileMenuAnchor(event.currentTarget);
  };

  const handleMobileMenuClose = () => {
    setMobileMenuAnchor(null);
  };

  const handleLogout = () => {
    dispatch(logout());
    handleProfileMenuClose();
    navigate('/');
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    handleProfileMenuClose();
    handleMobileMenuClose();
  };

  // ════════════════════════════════════════════════════════════════════════
  // 4-WORLD OS: Direct navigation to user's sovereign world
  // ════════════════════════════════════════════════════════════════════════
  const getUserWorldPath = (): string => {
    if (!user) return '/';
    return getLandingPathByRole(user);
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

  return (
    <AppBar
      position="sticky"
      elevation={1}
      sx={{
        bgcolor: 'white',
        color: 'text.primary',
        boxShadow: '0 1px 10px rgba(0, 0, 0, 0.08)',
        backdropFilter: 'blur(8px)',
      }}
    >
      <Container maxWidth="xl">
        <Toolbar
          sx={{
            minHeight: '64px !important',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            px: { xs: 2, md: 3 },
          }}
        >
          {/* Left Section - Logo & Brand */}
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              cursor: 'pointer',
              alignItems: { xs: 'flex-start', sm: 'flex-start' },
            }}
            onClick={() => navigate('/')}
          >
            <Typography
              variant="h6"
              component="div"
              sx={{
                fontWeight: 700,
                fontSize: '1.5rem',
                color: 'primary.main',
                lineHeight: 1.2,
              }}
            >
              CareerBridge
            </Typography>
            <Typography
              variant="caption"
              sx={{
                fontSize: '0.7rem',
                color: 'text.secondary',
                fontWeight: 500,
                lineHeight: 1,
                mt: 0.25,
              }}
            >
              Career clarity, guided execution
            </Typography>
          </Box>

          {/* Center Section - Navigation Links (Desktop) */}
          <Box
            component="nav"
            sx={{
              display: { xs: 'none', lg: 'flex' },
              gap: 2,
              flex: 1,
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            <Button
              color="inherit"
              onClick={() => navigate('/')}
              sx={{
                textTransform: 'none',
                fontWeight: 500,
                color: 'text.primary',
                fontSize: '0.938rem',
                '&:hover': { bgcolor: 'grey.50', color: 'primary.main' },
              }}
            >
              Home
            </Button>
            <Button
              color="inherit"
              onClick={() => navigate('/assessment')}
              sx={{
                textTransform: 'none',
                fontWeight: 500,
                color: 'text.primary',
                fontSize: '0.938rem',
                '&:hover': { bgcolor: 'grey.50', color: 'primary.main' },
              }}
            >
              Assessment Engine
            </Button>
            <Button
              color="inherit"
              onClick={() => navigate('/intelligence')}
              sx={{
                textTransform: 'none',
                fontWeight: 500,
                color: 'text.primary',
                fontSize: '0.938rem',
                '&:hover': { bgcolor: 'grey.50', color: 'primary.main' },
              }}
            >
              Market Intelligence
            </Button>
            <Button
              color="inherit"
              onClick={() => navigate('/mentors')}
              sx={{
                textTransform: 'none',
                fontWeight: 500,
                color: 'text.primary',
                fontSize: '0.938rem',
                '&:hover': { bgcolor: 'grey.50', color: 'primary.main' },
              }}
            >
              MentorBridge
            </Button>
            <Button
              color="inherit"
              onClick={() => navigate('/pricing')}
              sx={{
                textTransform: 'none',
                fontWeight: 500,
                color: 'text.primary',
                fontSize: '0.938rem',
                '&:hover': { bgcolor: 'grey.50', color: 'primary.main' },
              }}
            >
              Pricing
            </Button>
            <Button
              color="inherit"
              onClick={() => navigate('/resources')}
              sx={{
                textTransform: 'none',
                fontWeight: 500,
                color: 'text.primary',
                fontSize: '0.938rem',
                '&:hover': { bgcolor: 'grey.50', color: 'primary.main' },
              }}
            >
              Resources
            </Button>
          </Box>

          {/* Right Section - Auth Buttons / Avatar */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {isAuthenticated ? (
              <>
                {/* Notifications Bell */}
                <NotificationBell />

                {/* Desktop Avatar Menu */}
                <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center', gap: 1 }}>
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
                        cursor: 'pointer',
                      }}
                    >
                      {getUserInitials()}
                    </Avatar>
                  </IconButton>
                </Box>

                {/* Mobile Menu Button */}
                <IconButton
                  sx={{ display: { xs: 'flex', md: 'none' } }}
                  onClick={handleMobileMenuOpen}
                >
                  <MenuIcon />
                </IconButton>

                {/* Desktop Profile Menu */}
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
                  <MenuItem onClick={() => handleNavigation(getUserWorldPath())}>
                    <Dashboard sx={{ mr: 2, fontSize: 20 }} />
                    My World
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

                {/* Mobile Menu */}
                <Menu
                  anchorEl={mobileMenuAnchor}
                  open={Boolean(mobileMenuAnchor)}
                  onClose={handleMobileMenuClose}
                  anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'right',
                  }}
                  transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                  }}
                >
                  <MenuItem onClick={() => handleNavigation('/')}>Home</MenuItem>
                  <MenuItem onClick={() => handleNavigation('/assessment')}>Assessment Engine</MenuItem>
                  <MenuItem onClick={() => handleNavigation('/intelligence')}>Market Intelligence</MenuItem>
                  <MenuItem onClick={() => handleNavigation('/mentors')}>MentorBridge</MenuItem>
                  <Divider />
                  <MenuItem onClick={() => handleNavigation(getUserWorldPath())}>
                    <Dashboard sx={{ mr: 2, fontSize: 20 }} />
                    My World
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
              </>
            ) : (
              <>
                <Button
                  color="inherit"
                  onClick={() => navigate('/login')}
                  sx={{
                    textTransform: 'none',
                    fontWeight: 500,
                    color: 'text.primary',
                    fontSize: '0.938rem',
                    '&:hover': { bgcolor: 'grey.50' },
                  }}
                >
                  Sign In
                </Button>
                <Button
                  variant="contained"
                  onClick={() => navigate('/register')}
                  sx={{
                    textTransform: 'none',
                    fontWeight: 600,
                    background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
                    px: 3,
                    py: 1,
                    borderRadius: '8px',
                    boxShadow: '0 8px 18px rgba(25, 118, 210, 0.25)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #1565c0 0%, #0d47a1 100%)',
                      boxShadow: '0 12px 22px rgba(25, 118, 210, 0.3)',
                    },
                  }}
                >
                  Start Free Assessment
                </Button>
              </>
            )}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default PublicHeader;
