import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box } from '@mui/material';
import DashboardHeader from './DashboardHeader';

/**
 * DashboardLayout - For logged-in users and internal tools
 * Includes DashboardHeader only (NO footer, NO public navigation)
 */
const DashboardLayout: React.FC = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        bgcolor: '#F8FAFC', // Neutral SaaS background
      }}
    >
      {/* Dashboard Header - compact, no public navigation */}
      <DashboardHeader />

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: '100%',
          bgcolor: '#F8FAFC',
        }}
      >
        <Outlet />
      </Box>

      {/* NO FOOTER - Dashboard pages should not show public footer */}
    </Box>
  );
};

export default DashboardLayout;

