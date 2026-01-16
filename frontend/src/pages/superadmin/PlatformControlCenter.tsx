import React from 'react';
import { Container, Box, Typography, Alert, Card, CardContent } from '@mui/material';
import { Security as SecurityIcon, Construction as ConstructionIcon } from '@mui/icons-material';

/**
 * Platform Control Center
 * Main governance management interface
 */
const PlatformControlCenter: React.FC = () => {
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
          Platform Control Center
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Kernel governance and feature flag management
        </Typography>
      </Box>

      {/* Placeholder */}
      <Card>
        <CardContent sx={{ py: 8, textAlign: 'center' }}>
          <ConstructionIcon sx={{ fontSize: 80, color: 'warning.main', mb: 3 }} />
          
          <Typography variant="h5" fontWeight="bold" gutterBottom>
            Governance UI Coming Soon
          </Typography>
          
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto', mt: 2 }}>
            The Platform Control Center UI is under development. For now, governance changes can be made via:
          </Typography>

          <Box sx={{ mt: 4, p: 3, bgcolor: 'grey.50', borderRadius: 2, maxWidth: 700, mx: 'auto', textAlign: 'left' }}>
            <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
              # Backend API Endpoints (SuperAdmin only):<br /><br />
              GET  /api/v1/adminpanel/governance/platform-state/<br />
              PATCH /api/v1/adminpanel/governance/platform-state/<br /><br />
              GET  /api/v1/adminpanel/governance/feature-flags/<br />
              PATCH /api/v1/adminpanel/governance/feature-flags/&#123;key&#125;/<br /><br />
              # Django Admin:<br />
              /admin/kernel/platformstate/<br />
              /admin/kernel/featureflag/<br />
              /admin/kernel/governanceaudit/
            </Typography>
          </Box>

          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 4 }}>
            All governance changes require a reason field and create immutable audit entries.
          </Typography>
        </CardContent>
      </Card>
    </Container>
  );
};

export default PlatformControlCenter;
