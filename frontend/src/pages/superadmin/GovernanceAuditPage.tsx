import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Card,
  CardContent,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from '@mui/material';
import {
  Security as SecurityIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const GovernanceAuditPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);
  const [loading, setLoading] = useState(true);
  const [selectedAudit, setSelectedAudit] = useState<any | null>(null);

  // Check if user is superuser
  const isSuperUser = Boolean(user?.is_superuser);

  useEffect(() => {
    if (!isSuperUser) {
      navigate('/admin');
      return;
    }

    // TODO: Fetch governance audit logs from backend
    // For now, just stop loading
    setLoading(false);
  }, [isSuperUser, navigate]);

  const handleViewDetails = (audit: any) => {
    setSelectedAudit(audit);
  };

  const handleCloseDialog = () => {
    setSelectedAudit(null);
  };

  if (loading) {
    return <LoadingSpinner message="Loading governance audit logs..." />;
  }

  // Mock data for now
  const auditLogs: any[] = [];

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
          Governance Audit Logs
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Immutable audit trail of all kernel governance changes
        </Typography>
      </Box>

      {/* Audit Logs Table */}
      <Card>
        <CardContent>
          {auditLogs.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Typography variant="body1" color="text.secondary">
                No governance audit logs found.
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Audit entries will appear here when governance changes are made.
              </Typography>
            </Box>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>Action</TableCell>
                    <TableCell>Actor</TableCell>
                    <TableCell>Reason</TableCell>
                    <TableCell>Details</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {auditLogs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>{new Date(log.created_at).toLocaleString()}</TableCell>
                      <TableCell>
                        <Chip label={log.action} size="small" color="primary" />
                      </TableCell>
                      <TableCell>{log.actor || 'System'}</TableCell>
                      <TableCell>{log.reason}</TableCell>
                      <TableCell>
                        <IconButton size="small" onClick={() => handleViewDetails(log)}>
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Details Dialog */}
      <Dialog open={!!selectedAudit} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>Audit Entry Details</DialogTitle>
        <DialogContent>
          {selectedAudit && (
            <Box>
              <Typography variant="body2" color="text.secondary">
                Action: <strong>{selectedAudit.action}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Actor: <strong>{selectedAudit.actor || 'System'}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Timestamp: <strong>{new Date(selectedAudit.created_at).toLocaleString()}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Payload:
              </Typography>
              <Paper sx={{ p: 2, mt: 1, bgcolor: 'grey.50' }}>
                <pre style={{ margin: 0, fontSize: '0.75rem', overflow: 'auto' }}>
                  {JSON.stringify(selectedAudit.payload, null, 2)}
                </pre>
              </Paper>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default GovernanceAuditPage;
