import React from 'react';
import { Box, Typography } from '@mui/material';

const TermsPage: React.FC = () => {
  return (
    <Box sx={{ width: '100%', maxWidth: '1200px', mx: 'auto', px: { xs: 2, sm: 3, md: 6 }, py: { xs: 4, md: 6 } }}>
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: { xs: 6, md: 8 },
          px: { xs: 3, md: 4 },
          borderRadius: { xs: 0, md: 3 },
          mb: 8,
          textAlign: 'center',
        }}
      >
        <Typography
          variant="h2"
          component="h1"
          sx={{
            fontWeight: 700,
            fontSize: { xs: '2rem', md: '3rem' },
            color: 'white',
            mb: 2,
          }}
        >
          Terms of Service
        </Typography>
        <Typography
          variant="h5"
          sx={{
            fontSize: { xs: '1rem', md: '1.25rem' },
            color: 'rgba(255, 255, 255, 0.95)',
          }}
        >
          Last updated: January 2025
        </Typography>
      </Box>

      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
          1. Acceptance of Terms
        </Typography>
        <Typography variant="body1" sx={{ lineHeight: 1.8, mb: 4 }}>
          By accessing and using CareerBridge, you accept and agree to be bound by the terms and provision of this agreement.
        </Typography>

        <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
          2. Use License
        </Typography>
        <Typography variant="body1" sx={{ lineHeight: 1.8, mb: 4 }}>
          Permission is granted to temporarily use CareerBridge for personal, non-commercial transitory viewing only. 
          This is the grant of a license, not a transfer of title.
        </Typography>

        <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
          3. User Accounts
        </Typography>
        <Typography variant="body1" sx={{ lineHeight: 1.8, mb: 4 }}>
          You are responsible for maintaining the confidentiality of your account and password. You agree to accept 
          responsibility for all activities that occur under your account.
        </Typography>

        <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
          4. Service Availability
        </Typography>
        <Typography variant="body1" sx={{ lineHeight: 1.8, mb: 4 }}>
          CareerBridge reserves the right to modify, suspend, or discontinue any part of the service at any time 
          without prior notice.
        </Typography>
      </Box>
    </Box>
  );
};

export default TermsPage;

