import React from 'react';
import { Box, Typography } from '@mui/material';

const PrivacyPage: React.FC = () => {
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
          Privacy Policy
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
          1. Information We Collect
        </Typography>
        <Typography variant="body1" sx={{ lineHeight: 1.8, mb: 4 }}>
          We collect information that you provide directly to us, including your name, email address, resume data, 
          and career preferences when you use our services.
        </Typography>

        <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
          2. How We Use Your Information
        </Typography>
        <Typography variant="body1" sx={{ lineHeight: 1.8, mb: 4 }}>
          We use the information we collect to provide, maintain, and improve our services, process your requests, 
          and communicate with you about your account and our services.
        </Typography>

        <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
          3. Information Sharing
        </Typography>
        <Typography variant="body1" sx={{ lineHeight: 1.8, mb: 4 }}>
          We do not sell your personal information. We may share your information with mentors you choose to connect 
          with, and with service providers who assist us in operating our platform.
        </Typography>

        <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
          4. Data Security
        </Typography>
        <Typography variant="body1" sx={{ lineHeight: 1.8, mb: 4 }}>
          We implement appropriate technical and organizational measures to protect your personal information against 
          unauthorized access, alteration, disclosure, or destruction.
        </Typography>
      </Box>
    </Box>
  );
};

export default PrivacyPage;

