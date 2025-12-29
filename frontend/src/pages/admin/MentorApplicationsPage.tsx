import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  TextField,
  Button,
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  Alert,
  Avatar,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Search as SearchIcon,
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Visibility as ViewIcon,
  ExpandMore as ExpandMoreIcon,
  Work as WorkIcon,
  Email as EmailIcon,
} from '@mui/icons-material';

import LoadingSpinner from '../../components/common/LoadingSpinner';
import SkeletonLoader from '../../components/common/SkeletonLoader';
import adminService from '../../services/api/adminService';

interface MentorApplication {
  id: number;
  user_id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  status: 'pending' | 'approved' | 'rejected';
  motivation: string;
  relevant_experience: string;
  preferred_payment_method: string;
  created_at: string;
  reviewed_at?: string;
  reviewed_by?: string;
}

const MentorApplicationsPage: React.FC = () => {
  const [applications, setApplications] = useState<MentorApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedApplication, setSelectedApplication] = useState<MentorApplication | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState<'view' | 'approve' | 'reject'>('view');
  const [rejectionReason, setRejectionReason] = useState('');

  useEffect(() => {
    fetchApplications();
  }, [page, searchTerm, statusFilter, pageSize]);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      const params: any = { page, page_size: pageSize };
      if (statusFilter !== 'all') params.status = statusFilter;
      if (searchTerm) params.search = searchTerm;
      
      const data = await adminService.getMentorApplications(params);
      if (Array.isArray(data)) {
        setApplications(data);
        setTotalPages(1);
        setTotalCount(data.length);
      } else if (data?.results && Array.isArray(data.results)) {
        setApplications(data.results);
        setTotalPages(data.total_pages || Math.ceil((data.count || 0) / (data.page_size || 10)) || 1);
        setTotalCount(data.count || data.results.length);
      } else {
        setApplications([]);
        setTotalPages(1);
        setTotalCount(0);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load applications');
      console.error('Error fetching applications:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    setPage(1);
  };

  const handleStatusFilterChange = (event: any) => {
    setStatusFilter(event.target.value);
    setPage(1);
  };

  const handlePageSizeChange = (event: any) => {
    setPageSize(event.target.value);
    setPage(1);
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const handleApplicationAction = (application: MentorApplication, action: 'view' | 'approve' | 'reject') => {
    setSelectedApplication(application);
    setDialogType(action);
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    setSelectedApplication(null);
    setRejectionReason('');
  };

  const handleConfirmAction = async () => {
    if (!selectedApplication) return;

    try {
      switch (dialogType) {
        case 'approve':
          await adminService.approveMentorApplication(selectedApplication.id);
          setSuccess('Application approved successfully');
          break;
        case 'reject':
          await adminService.rejectMentorApplication(selectedApplication.id, rejectionReason);
          setSuccess('Application rejected successfully');
          break;
      }
      handleDialogClose();
      fetchApplications(); // Refresh the list
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to perform action');
      console.error('Error performing action:', err);
    }
  };

  const getStatusChip = (status: string) => {
    switch (status) {
      case 'pending':
        return <Chip label="Pending" color="warning" size="small" />;
      case 'approved':
        return <Chip label="Approved" color="success" size="small" />;
      case 'rejected':
        return <Chip label="Rejected" color="error" size="small" />;
      default:
        return <Chip label={status} color="default" size="small" />;
    }
  };

  if (loading && applications.length === 0) {
    return <LoadingSpinner message="Loading applications..." />;
  }

  return (
    <>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Mentor Applications
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Review and manage mentor applications ({totalCount})
        </Typography>
      </Box>

      <Box>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
              <TextField
                placeholder="Search applications..."
                value={searchTerm}
                onChange={handleSearch}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
                sx={{ minWidth: 300 }}
              />
              <FormControl sx={{ minWidth: 150 }}>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={handleStatusFilterChange}
                >
                  <MenuItem value="all">All Applications</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="approved">Approved</MenuItem>
                  <MenuItem value="rejected">Rejected</MenuItem>
                </Select>
              </FormControl>
              <FormControl sx={{ minWidth: 150 }}>
                <InputLabel>Page Size</InputLabel>
                <Select
                  value={pageSize}
                  label="Page Size"
                  onChange={handlePageSizeChange}
                >
                  <MenuItem value={10}>10</MenuItem>
                  <MenuItem value={20}>20</MenuItem>
                  <MenuItem value={50}>50</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Applications ({applications.length})</Typography>
            </Box>

            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Applicant</TableCell>
                    <TableCell>Motivation</TableCell>
                    <TableCell>Experience</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Submitted</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={6}>
                        <SkeletonLoader type="table" count={3} />
                      </TableCell>
                    </TableRow>
                  ) : (
                    applications.map((application) => (
                      <TableRow key={application.id} hover>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Avatar sx={{ mr: 2, width: 32, height: 32 }}>
                              {application.first_name.charAt(0)}
                            </Avatar>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {application.first_name} {application.last_name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {application.email}
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {application.motivation.substring(0, 50)}...
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {application.relevant_experience.substring(0, 50)}...
                          </Typography>
                        </TableCell>
                        <TableCell>{getStatusChip(application.status)}</TableCell>
                        <TableCell>
                          {new Date(application.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={() => handleApplicationAction(application, 'view')}
                            color="primary"
                          >
                            <ViewIcon />
                          </IconButton>
                          {application.status === 'pending' && (
                            <>
                              <IconButton
                                size="small"
                                onClick={() => handleApplicationAction(application, 'approve')}
                                color="success"
                              >
                                <ApproveIcon />
                              </IconButton>
                              <IconButton
                                size="small"
                                onClick={() => handleApplicationAction(application, 'reject')}
                                color="error"
                              >
                                <RejectIcon />
                              </IconButton>
                            </>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>

            {totalPages > 1 && (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                <Pagination
                  count={totalPages}
                  page={page}
                  onChange={handlePageChange}
                  color="primary"
                />
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>

      {/* Application Detail Dialog */}
      <Dialog open={dialogOpen} onClose={handleDialogClose} maxWidth="md" fullWidth>
        <DialogTitle>
          {dialogType === 'view' && 'Application Details'}
          {dialogType === 'approve' && 'Approve Application'}
          {dialogType === 'reject' && 'Reject Application'}
        </DialogTitle>
        <DialogContent>
          {selectedApplication && (
            <Box>
              {dialogType === 'view' && (
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                    <Avatar sx={{ mr: 2, width: 64, height: 64 }}>
                      {selectedApplication.first_name.charAt(0)}
                    </Avatar>
                    <Box>
                      <Typography variant="h6">
                        {selectedApplication.first_name} {selectedApplication.last_name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {selectedApplication.email}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        @{selectedApplication.username}
                      </Typography>
                    </Box>
                  </Box>

                  <Accordion defaultExpanded>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="h6">Basic Information</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        <strong>Motivation:</strong> {selectedApplication.motivation}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        <strong>Relevant Experience:</strong> {selectedApplication.relevant_experience}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        <strong>Preferred Payment Method:</strong> {selectedApplication.preferred_payment_method}
                      </Typography>
                    </AccordionDetails>
                  </Accordion>


                </Box>
              )}

              {dialogType === 'reject' && (
                <Box>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    Please provide a reason for rejecting this application:
                  </Typography>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    placeholder="Enter rejection reason..."
                    variant="outlined"
                  />
                </Box>
              )}

              {dialogType === 'approve' && (
                <Typography>
                  Are you sure you want to approve {selectedApplication.first_name} {selectedApplication.last_name}'s mentor application?
                </Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>Cancel</Button>
          {dialogType === 'approve' && (
            <Button onClick={handleConfirmAction} color="success" variant="contained">
              Approve
            </Button>
          )}
          {dialogType === 'reject' && (
            <Button 
              onClick={handleConfirmAction} 
              color="error" 
              variant="contained"
              disabled={!rejectionReason.trim()}
            >
              Reject
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </>
  );
};

export default MentorApplicationsPage; 
