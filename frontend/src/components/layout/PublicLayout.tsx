import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box } from '@mui/material';
import PublicHeader from './PublicHeader';
import Footer from '../common/Footer';
import SkipLink from '../common/SkipLink';

/**
 * PublicLayout - For marketing and public-facing pages
 * Includes PublicHeader and PublicFooter
 */
const PublicLayout: React.FC = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        bgcolor: 'background.default',
        color: 'text.primary',
      }}
    >
      <SkipLink />

      {/* Public Header with marketing navigation */}
      <PublicHeader />

      {/* Main Content Area */}
      <Box
        component="main"
        id="main-content"
        tabIndex={-1}
        sx={{
          flexGrow: 1,
          width: '100%',
          '&:focus': { outline: 'none' },
        }}
      >
        <Outlet />
      </Box>

      {/* Public Footer with links and company info */}
      <Footer />
    </Box>
  );
};

export default PublicLayout;
