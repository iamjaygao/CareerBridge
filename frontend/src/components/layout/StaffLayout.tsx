import React, { useState } from 'react';
import { Box } from '@mui/material';
import StaffSidebar from './StaffSidebar';
import StaffTopbar from './StaffTopbar';

interface StaffLayoutProps {
  children: React.ReactNode;
}

const StaffLayout: React.FC<StaffLayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'grey.50' }}>
      {/* Staff Sidebar */}
      <StaffSidebar mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} />

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
        {/* Staff Topbar */}
        <StaffTopbar onMenuClick={handleDrawerToggle} />

        {/* Page content */}
        <Box
          sx={{
            flexGrow: 1,
            p: { xs: 2, sm: 3, md: 4 },
            bgcolor: 'grey.50',
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default StaffLayout;

