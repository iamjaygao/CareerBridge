import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box } from '@mui/material';
import Header from '../common/Header';
import Footer from '../common/Footer';

const Layout: React.FC = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        bgcolor: 'background.default',
      }}
    >
      {/* Global Header */}
      <Header />

      {/* Main Content Area - Outlet renders child routes */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: '100%',
        }}
      >
        <Outlet />
      </Box>

      {/* Global Footer */}
      <Footer />
    </Box>
  );
};

export default Layout;

