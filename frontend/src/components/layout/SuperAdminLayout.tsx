import React, { useState } from 'react';
import { Box } from '@mui/material';
import SuperAdminSidebar from './SuperAdminSidebar';
import SuperAdminTopbar from './SuperAdminTopbar';

interface SuperAdminLayoutProps {
  children: React.ReactNode;
}

const SuperAdminLayout: React.FC<SuperAdminLayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: '#F8FAFC' }}>
      {/* SuperAdmin Sidebar */}
      <SuperAdminSidebar mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} />

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
        {/* SuperAdmin Topbar */}
        <SuperAdminTopbar onMenuClick={handleDrawerToggle} />

        {/* Page content */}
        <Box
          sx={{
            flexGrow: 1,
            p: { xs: 2, sm: 3, md: 4 },
            bgcolor: '#F8FAFC',
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default SuperAdminLayout;

