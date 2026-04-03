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
  ElectricBolt,
  Tune,
  Dashboard,
  Terminal,
  Monitor,
  Settings,
  People,
  School,
  CalendarToday,
  Work,
  FactCheck,
  VideocamOutlined,
  PlayCircleOutline,
  Dns,
  Security,
} from '@mui/icons-material';

const drawerWidth = 260;

interface MenuItem {
  text: string;
  icon: React.ReactElement;
  path: string;
  disabled?: boolean;
}

interface MenuSection {
  title: string;
  items: MenuItem[];
}

interface SuperAdminSidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

const SuperAdminSidebar: React.FC<SuperAdminSidebarProps> = ({ mobileOpen, onMobileClose }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuSections: MenuSection[] = [
    {
      title: 'Kernel Control Plane',
      items: [
        { text: 'Kernel Pulse',              icon: <MonitorHeart />,      path: '/superadmin/kernel-pulse' },
        { text: 'Workload Runtime Console',  icon: <Rocket />,            path: '/superadmin/workload-runtime' },
        { text: 'Governance Audit Logs',     icon: <History />,           path: '/superadmin/audit-logs' },
        { text: 'Bus Power Control',         icon: <ElectricBolt />,      path: '/superadmin/bus-power' },
        { text: 'Governance Control',        icon: <Tune />,              path: '/superadmin/governance-control' },
      ],
    },
    {
      title: 'Platform Overview',
      items: [
        { text: 'Dashboard',                 icon: <Dashboard />,         path: '/superadmin/dashboard' },
        { text: 'Command Center',            icon: <Terminal />,          path: '/superadmin/command-center' },
        { text: 'OS Status',                 icon: <Monitor />,           path: '/superadmin/os-status' },
        { text: 'Platform Control Center',   icon: <Settings />,          path: '/superadmin/platform-control' },
      ],
    },
    {
      title: 'User Management',
      items: [
        { text: 'Users',                     icon: <People />,            path: '/superadmin/users' },
        { text: 'Mentors',                   icon: <School />,            path: '/superadmin/mentors' },
        { text: 'Appointments',              icon: <CalendarToday />,     path: '/superadmin/appointments' },
        { text: 'Jobs',                      icon: <Work />,              path: '/superadmin/jobs' },
        { text: 'Assessments',               icon: <FactCheck />,         path: '/superadmin/assessments' },
      ],
    },
    {
      title: 'Peer Mock',
      items: [
        { text: 'Peer Mock Console',         icon: <VideocamOutlined />,  path: '/superadmin/peer-mock' },
        { text: 'Peer Mock Runtime',         icon: <PlayCircleOutline />, path: '/superadmin/peer-mock-runtime' },
      ],
    },
    {
      title: 'System',
      items: [
        { text: 'System Console',            icon: <Dns />,               path: '/superadmin/system' },
        { text: 'System Audit',              icon: <Security />,          path: '/superadmin/system-audit' },
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
          sx={{ color: 'white', fontWeight: 700, fontSize: '1.15rem' }}
        >
          CareerBridge OS v2
        </Typography>
      </Toolbar>
      <Divider />

      {menuSections.map((section, sectionIndex) => (
        <React.Fragment key={sectionIndex}>
          <List sx={{ px: 2, py: 1 }}>
            <ListSubheader
              sx={{
                bgcolor: 'transparent',
                fontSize: '0.7rem',
                fontWeight: 700,
                color: 'text.secondary',
                lineHeight: '28px',
                px: 2,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
              }}
            >
              {section.title}
            </ListSubheader>
            {section.items.map((item) => {
              const isSelected =
                location.pathname === item.path ||
                (item.path !== '/superadmin' && location.pathname.startsWith(item.path));

              return (
                <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
                  <ListItemButton
                    onClick={() => {
                      if (item.disabled !== true) {
                        navigate(item.path);
                        onMobileClose();
                      }
                    }}
                    selected={isSelected}
                    disabled={item.disabled === true}
                    sx={{
                      borderRadius: 2,
                      '&.Mui-selected': {
                        bgcolor: 'primary.main',
                        color: 'white',
                        '&:hover': { bgcolor: 'primary.dark' },
                        '& .MuiListItemIcon-root': { color: 'white' },
                      },
                      '&:hover': {
                        bgcolor: item.disabled === true ? 'transparent' : 'grey.100',
                      },
                      '&.Mui-disabled': { opacity: 0.5 },
                    }}
                  >
                    <ListItemIcon
                      sx={{ color: isSelected ? 'white' : 'text.secondary', minWidth: 40 }}
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
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
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
            overflowY: 'auto',
          },
        }}
        open
      >
        {drawer}
      </Drawer>
    </>
  );
};

export default SuperAdminSidebar;
