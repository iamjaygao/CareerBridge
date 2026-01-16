/**
 * Kernel World Sidebar (Phase-A UI Constitution)
 * 
 * Purpose:
 * - Kernel Control Plane menu only
 * - Exactly 3 menu items (as per Phase-A UI Constitution)
 * - No business world menu items
 * 
 * Allowed Menu Items:
 * 1. Kernel Pulse (Observability)
 * 2. Workload Runtime Console (Frozen Registry)
 * 3. Governance Audit Logs (Compliance)
 */

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Divider,
  ListSubheader,
} from '@mui/material';
import {
  MonitorHeart,
  Rocket,
  History,
} from '@mui/icons-material';

const drawerWidth = 260;

interface MenuItem {
  text: string;
  icon: React.ReactElement;
  path: string;
}

interface MenuSection {
  title: string;
  items: MenuItem[];
}

interface KernelWorldSidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

const KernelWorldSidebar: React.FC<KernelWorldSidebarProps> = ({ mobileOpen, onMobileClose }) => {
  const navigate = useNavigate();
  const location = useLocation();

  // Phase-A UI Constitution: Only 3 allowed UI elements in Kernel Control Plane
  const menuSections: MenuSection[] = [
    {
      title: '🔷 GateAI OS Kernel Control Plane',
      items: [
        { 
          text: 'Kernel Pulse', 
          icon: <MonitorHeart />, 
          path: '/superadmin/kernel-pulse',
        },
        { 
          text: 'Workload Runtime Console', 
          icon: <Rocket />, 
          path: '/superadmin/workload-runtime',
        },
        { 
          text: 'Governance Audit Logs', 
          icon: <History />, 
          path: '/superadmin/audit-logs',
        },
      ],
    },
  ];

  const drawer = (
    <Box>
      <Toolbar
        sx={{
          px: 3,
          py: 2,
          bgcolor: 'primary.main',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}
      >
        <Typography
          variant="h6"
          noWrap
          component="div"
          sx={{
            color: 'white',
            fontWeight: 700,
            fontSize: '1.15rem',
          }}
        >
          CareerBridge OS
        </Typography>
      </Toolbar>
      <Divider />

      {/* Kernel World Menu Sections */}
      {menuSections.map((section, sectionIndex) => (
        <React.Fragment key={sectionIndex}>
          <List sx={{ px: 2, py: 1 }}>
            <ListSubheader
              sx={{
                bgcolor: 'transparent',
                fontSize: '0.75rem',
                fontWeight: 700,
                color: 'text.secondary',
                lineHeight: '32px',
                px: 2,
              }}
            >
              {section.title}
            </ListSubheader>
            {section.items.map((item) => {
              const isSelected = location.pathname === item.path || 
                (item.path !== '/superadmin' && location.pathname.startsWith(item.path));
              
              return (
                <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
                  <ListItemButton
                    onClick={() => {
                      navigate(item.path);
                      onMobileClose();
                    }}
                    selected={isSelected}
                    sx={{
                      borderRadius: 2,
                      '&.Mui-selected': {
                        bgcolor: 'primary.main',
                        color: 'white',
                        '&:hover': {
                          bgcolor: 'primary.dark',
                        },
                        '& .MuiListItemIcon-root': {
                          color: 'white',
                        },
                      },
                      '&:hover': {
                        bgcolor: 'grey.100',
                      },
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        color: isSelected ? 'white' : 'text.secondary',
                        minWidth: 40,
                      }}
                    >
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.text}
                      primaryTypographyProps={{
                        fontWeight: isSelected ? 600 : 500,
                        fontSize: '0.875rem',
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              );
            })}
          </List>
          {sectionIndex < menuSections.length - 1 && <Divider sx={{ my: 1 }} />}
        </React.Fragment>
      ))}
    </Box>
  );

  return (
    <>
      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onMobileClose}
        ModalProps={{
          keepMounted: true,
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
          },
        }}
      >
        {drawer}
      </Drawer>
      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
            position: 'relative',
            height: '100vh',
            borderRight: '1px solid',
            borderColor: 'divider',
          },
        }}
        open
      >
        {drawer}
      </Drawer>
    </>
  );
};

export default KernelWorldSidebar;
