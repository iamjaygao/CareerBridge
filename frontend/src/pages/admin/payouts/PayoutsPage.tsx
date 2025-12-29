import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../../components/common/LoadingSpinner';
import ErrorAlert from '../../../components/common/ErrorAlert';
import adminService from '../../../services/api/adminService';
import { handleApiError } from '../../../services/utils/errorHandler';
import type { ApiError } from '../../../services/utils/errorHandler';

interface Payout {
  id: number;
  mentor: {
    id: number;
    name: string;
    email: string;
  };
  amount: number;
  status: 'pending' | 'approved' | 'rejected' | 'completed';
  requested_at: string;
  processed_at?: string;
  notes?: string;
}

const PayoutsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [payouts, setPayouts] = useState<Payout[]>([]);
  const [selectedPayout, setSelectedPayout] = useState<Payout | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'approve' | 'reject' | 'view'>('view');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    const fetchPayouts = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await adminService.getPayouts();
        
        // Handle different response formats
        let payoutsList: Payout[] = [];
        if (Array.isArray(data)) {
          payoutsList = data;
        } else if (data.results && Array.isArray(data.results)) {
          payoutsList = data.results;
        } else if (data.data && Array.isArray(data.data)) {
          payoutsList = data.data;
        }
        
        // Normalize payout objects to match interface
        const normalizedPayouts = payoutsList.map((p: any) => ({
          id: p.id,
          mentor: {
            id: p.mentor?.id || p.mentor_id || 0,
            name: p.mentor?.name || p.mentor_name || 'Unknown',
            email: p.mentor?.email || p.mentor_email || '',
          },
          amount: p.amount || 0,
          status: p.status || 'pending',
          requested_at: p.requested_at || p.created_at || new Date().toISOString(),
          processed_at: p.processed_at,
          notes: p.notes,
        }));
        
        setPayouts(normalizedPayouts);
      } catch (err: any) {
        setError(handleApiError(err));
        console.error('Failed to fetch payouts:', err);
        setPayouts([]);
      } finally {
        setLoading(false);
      }
    };

    fetchPayouts();
  }, []);

  const handleAction = (payout: Payout, type: 'approve' | 'reject' | 'view') => {
    setSelectedPayout(payout);
    setActionType(type);
    setDialogOpen(true);
    setNotes('');
  };

  const handleConfirm = async () => {
    if (!selectedPayout) return;

    try {
      if (actionType === 'approve') {
        await adminService.approvePayout(selectedPayout.id, notes);
      } else if (actionType === 'reject') {
        await adminService.rejectPayout(selectedPayout.id, notes);
      }
      
      // Refresh payouts list
      const data = await adminService.getPayouts();
      let payoutsList: Payout[] = [];
      if (Array.isArray(data)) {
        payoutsList = data;
      } else if (data.results && Array.isArray(data.results)) {
        payoutsList = data.results;
      } else if (data.data && Array.isArray(data.data)) {
        payoutsList = data.data;
      }
      
      const normalizedPayouts = payoutsList.map((p: any) => ({
        id: p.id,
        mentor: {
          id: p.mentor?.id || p.mentor_id || 0,
          name: p.mentor?.name || p.mentor_name || 'Unknown',
          email: p.mentor?.email || p.mentor_email || '',
        },
        amount: p.amount || 0,
        status: p.status || 'pending',
        requested_at: p.requested_at || p.created_at || new Date().toISOString(),
        processed_at: p.processed_at,
        notes: p.notes,
      }));
      
      setPayouts(normalizedPayouts);
      setDialogOpen(false);
      setSelectedPayout(null);
      setNotes('');
    } catch (err: any) {
      console.error('Failed to update payout:', err);
      const errorMessage = err?.response?.data?.detail 
        || err?.response?.data?.error
        || err?.message 
        || 'Failed to update payout';
      alert(errorMessage);
    }
  };

  const getStatusChip = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      pending: 'warning',
      approved: 'info',
      rejected: 'error',
      completed: 'success',
    };
    return <Chip label={status.charAt(0).toUpperCase() + status.slice(1)} color={colors[status] || 'default'} size="small" />;
  };

  if (loading) {
    return <LoadingSpinner message="Loading payouts..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Payout Management
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Review and approve mentor payouts
        </Typography>
      </Box>

      {error && (
        <ErrorAlert error={error} overrideMessage="Failed to load payouts." />
      )}

      {/* Stats Cards */}
      <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              ${payouts.filter(p => p.status === 'pending').reduce((sum, p) => sum + p.amount, 0).toFixed(2)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Pending Payouts
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {payouts.filter(p => p.status === 'pending').length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Pending Requests
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              ${payouts.filter(p => p.status === 'completed').reduce((sum, p) => sum + p.amount, 0).toFixed(2)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Paid This Month
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Payouts Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Mentor</TableCell>
                  <TableCell>Amount</TableCell>
                  <TableCell>Requested</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {payouts.map((payout) => (
                  <TableRow key={payout.id} hover>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {payout.mentor.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {payout.mentor.email}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        ${payout.amount.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {new Date(payout.requested_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {getStatusChip(payout.status)}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={() => handleAction(payout, 'view')}
                        color="primary"
                      >
                        <ViewIcon />
                      </IconButton>
                      {payout.status === 'pending' && (
                        <>
                          <IconButton
                            size="small"
                            onClick={() => handleAction(payout, 'approve')}
                            color="success"
                          >
                            <ApproveIcon />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleAction(payout, 'reject')}
                            color="error"
                          >
                            <RejectIcon />
                          </IconButton>
                        </>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Action Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {actionType === 'approve' && 'Approve Payout'}
          {actionType === 'reject' && 'Reject Payout'}
          {actionType === 'view' && 'Payout Details'}
        </DialogTitle>
        <DialogContent>
          {selectedPayout && (
            <Box sx={{ pt: 2 }}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">Mentor</Typography>
                <Typography variant="body1" fontWeight="medium">
                  {selectedPayout.mentor.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedPayout.mentor.email}
                </Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">Amount</Typography>
                <Typography variant="h6" fontWeight="medium">
                  ${selectedPayout.amount.toFixed(2)}
                </Typography>
              </Box>
              {(actionType === 'approve' || actionType === 'reject') && (
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Notes (optional)"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  sx={{ mt: 2 }}
                />
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          {(actionType === 'approve' || actionType === 'reject') && (
            <Button
              variant="contained"
              onClick={handleConfirm}
              color={actionType === 'approve' ? 'success' : 'error'}
            >
              {actionType === 'approve' ? 'Approve' : 'Reject'}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PayoutsPage;
