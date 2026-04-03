import React from 'react';
import { Container, Box, Typography, Alert } from '@mui/material';
import { Security as SecurityIcon } from '@mui/icons-material';

/**
 * System / Runtime Logs page
 * Redirects to existing system logs functionality
 */
const SystemAuditPage: React.FC = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* OS Warning Banner */}
      <Alert 
        severity="warning" 
        icon={<SecurityIcon />}
        sx={{ mb: 4, fontWeight: 600 }}
      >
        ⚠️ You are operating the CareerBridge OS Kernel. All actions are audited.
      </Alert>

      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          System / Runtime Logs
        </Typography>
        <Typography variant="body2" color="text.secondary">
          System operations and runtime audit trail
        </Typography>
      </Box>

      <Alert severity="info">
        System audit logs are available in the Kernel Operations Console.
        Navigate to Kernel Operations Console → System Logs section.
      </Alert>
    </Container>
  );
};

export default SystemAuditPage;
