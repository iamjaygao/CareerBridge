import React from 'react';
import { Container, Box, Typography, Card, CardContent, Alert } from '@mui/material';
import { Rocket as RocketIcon, Security as SecurityIcon } from '@mui/icons-material';

const PeerMockRuntimePage: React.FC = () => {
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
          Peer Mock Runtime Console
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Workload runtime control and monitoring
        </Typography>
      </Box>

      {/* Placeholder Card */}
      <Card>
        <CardContent sx={{ py: 8, textAlign: 'center' }}>
          <RocketIcon sx={{ fontSize: 80, color: 'primary.main', mb: 3 }} />
          
          <Typography variant="h5" fontWeight="bold" gutterBottom>
            Runtime Layer Coming Online
          </Typography>
          
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto', mt: 2 }}>
            The Peer Mock workload runtime console is being provisioned. The OS is booting the first workload infrastructure.
          </Typography>

          <Box sx={{ mt: 4, p: 3, bgcolor: 'grey.50', borderRadius: 2, maxWidth: 700, mx: 'auto' }}>
            <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
              [KERNEL] Initializing workload runtime layer...<br />
              [KERNEL] Phase-A: Single workload mode active<br />
              [KERNEL] Workload: PEER_MOCK<br />
              [KERNEL] Status: PROVISIONING<br />
              [KERNEL] Runtime console: PENDING
            </Typography>
          </Box>

          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 4 }}>
            This page will display runtime metrics, logs, and controls once the workload layer is deployed.
          </Typography>
        </CardContent>
      </Card>
    </Container>
  );
};

export default PeerMockRuntimePage;
