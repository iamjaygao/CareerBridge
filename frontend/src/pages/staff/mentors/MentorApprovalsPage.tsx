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
  Avatar,
  TextField,
  Alert,
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Visibility as ViewIcon,
  Description as DocumentIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../../components/common/LoadingSpinner';
import adminService from '../../../services/api/adminService';
import { useNotification } from '../../../components/common/NotificationProvider';

interface MentorApplication {
  id: number;
  name: string;
  email: string;
  experience_years: number;
  expertise: string[];
  motivation: string;
  status: 'pending' | 'approved' | 'rejected';
  submitted_at: string;
  documents?: string[];
}

const MentorApprovalsPage: React.FC = () => {
  const { showSuccess, showError } = useNotification();
  const [loading, setLoading] = useState(true);
  const [applications, setApplications] = useState<MentorApplication[]>([]);
  const [selectedApplication, setSelectedApplication] = useState<MentorApplication | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'approve' | 'reject' | 'view'>('view');
  const [rejectionReason, setRejectionReason] = useState('');

  useEffect(() => {
    const fetchApplications = async () => {
      try {
        const data = await adminService.getMentorApplications({ status: 'pending' });
        const list = Array.isArray(data) ? data : (data?.results || []);
        const mapped = list.map((app: any) => ({
          id: app.id,
          name: `${app.first_name || ''} ${app.last_name || ''}`.trim() || app.username,
          email: app.email,
          experience_years: app.years_of_experience || 0,
          expertise: app.expertise || [],
          motivation: app.motivation || app.relevant_experience || '',
          status: app.status,
          submitted_at: app.created_at,
          documents: [],
        }));
        setApplications(mapped);
      } catch {
        setApplications([]);
      } finally {
        setLoading(false);
      }
    };

    fetchApplications();
  }, []);

  const handleAction = (application: MentorApplication, type: 'approve' | 'reject' | 'view') => {
    setSelectedApplication(application);
    setActionType(type);
    setDialogOpen(true);
    setRejectionReason('');
  };

  const handleConfirm = async () => {
    if (!selectedApplication) return;

    try {
      if (actionType === 'approve') {
        await adminService.approveMentorApplication(selectedApplication.id);
        showSuccess('Mentor application approved.');
      } else if (actionType === 'reject') {
        await adminService.rejectMentorApplication(selectedApplication.id, rejectionReason);
        showSuccess('Mentor application rejected.');
      }
      setApplications(applications.filter(app => app.id !== selectedApplication.id));
    } catch {
      showError('Failed to update application.');
    }

    setDialogOpen(false);
    setSelectedApplication(null);
    setRejectionReason('');
  };

  const getStatusChip = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      pending: 'warning',
      approved: 'success',
      rejected: 'error',
    };
    return <Chip label={status.charAt(0).toUpperCase() + status.slice(1)} color={colors[status] || 'default'} size="small" />;
  };

  if (loading) {
    return <LoadingSpinner message="Loading mentor applications..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Mentor Approvals
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Review and approve mentor applications
        </Typography>
      </Box>

      {/* Applications Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Mentor</TableCell>
                  <TableCell>Experience</TableCell>
                  <TableCell>Expertise</TableCell>
                  <TableCell>Application Info</TableCell>
                  <TableCell>Documents</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {applications.map((application) => (
                  <TableRow key={application.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Avatar sx={{ mr: 2, width: 40, height: 40 }}>
                          {application.name.charAt(0)}
                        </Avatar>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {application.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {application.email}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {application.experience_years} years
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {application.expertise.slice(0, 2).map((exp, idx) => (
                          <Chip key={idx} label={exp} size="small" variant="outlined" />
                        ))}
                        {application.expertise.length > 2 && (
                          <Chip label={`+${application.expertise.length - 2}`} size="small" />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                        {application.motivation.substring(0, 50)}...
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {application.documents && application.documents.length > 0 ? (
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <DocumentIcon sx={{ fontSize: 20, color: 'text.secondary' }} />
                          <Typography variant="caption">
                            {application.documents.length} file(s)
                          </Typography>
                        </Box>
                      ) : (
                        <Typography variant="caption" color="text.secondary">
                          No documents
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {getStatusChip(application.status)}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={() => handleAction(application, 'view')}
                        color="primary"
                      >
                        <ViewIcon />
                      </IconButton>
                      {application.status === 'pending' && (
                        <>
                          <IconButton
                            size="small"
                            onClick={() => handleAction(application, 'approve')}
                            color="success"
                          >
                            <ApproveIcon />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleAction(application, 'reject')}
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
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {actionType === 'approve' && 'Approve Mentor Application'}
          {actionType === 'reject' && 'Reject Mentor Application'}
          {actionType === 'view' && 'Application Details'}
        </DialogTitle>
        <DialogContent>
          {selectedApplication && (
            <Box sx={{ pt: 2 }}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">Mentor</Typography>
                <Typography variant="body1" fontWeight="medium">
                  {selectedApplication.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedApplication.email}
                </Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">Experience</Typography>
                <Typography variant="body1">
                  {selectedApplication.experience_years} years
                </Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">Expertise</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                  {selectedApplication.expertise.map((exp, idx) => (
                    <Chip key={idx} label={exp} size="small" />
                  ))}
                </Box>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">Motivation</Typography>
                <Typography variant="body1" sx={{ mt: 0.5 }}>
                  {selectedApplication.motivation}
                </Typography>
              </Box>
              {actionType === 'reject' && (
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Rejection Reason (required)"
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  sx={{ mt: 2 }}
                  required
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
              disabled={actionType === 'reject' && !rejectionReason.trim()}
            >
              {actionType === 'approve' ? 'Approve' : 'Reject'}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MentorApprovalsPage;
