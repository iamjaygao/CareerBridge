import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import { Assessment as AssessmentIcon } from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import adminService from '../../services/api/adminService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import { handleApiError } from '../../services/utils/errorHandler';
import type { ApiError } from '../../services/utils/errorHandler';

const AssessmentPage: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [stats, setStats] = useState({
    totalAssessments: 0,
    totalResumes: 0,
  });
  const [assessments, setAssessments] = useState<any[]>([]);

  useEffect(() => {
    const fetchAssessmentData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const [statsData, assessmentsData] = await Promise.all([
          adminService.getAssessmentStats(),
          adminService.getAssessments({ limit: 10 }),
        ]);
        
        setStats({
          totalAssessments: statsData.total_assessments || statsData.totalAssessments || 0,
          totalResumes: statsData.total_resumes || statsData.totalResumes || 0,
        });
        
        // Handle different response formats
        let assessmentsList: any[] = [];
        if (Array.isArray(assessmentsData)) {
          assessmentsList = assessmentsData;
        } else if (assessmentsData.results && Array.isArray(assessmentsData.results)) {
          assessmentsList = assessmentsData.results;
        } else if (assessmentsData.data && Array.isArray(assessmentsData.data)) {
          assessmentsList = assessmentsData.data;
        }
        
        setAssessments(assessmentsList);
      } catch (err: any) {
        setError(handleApiError(err));
        console.error('Failed to fetch assessment data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAssessmentData();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading assessment data..." />;
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <ErrorAlert error={error} overrideMessage="Failed to load assessment data." />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
          Assessment Engine (Read-Only)
        </Typography>
        <Typography variant="body1" color="text.secondary">
          View assessment results and statistics
        </Typography>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        Admin has read-only access to assessment data. Only SuperAdmin can modify prompts and configuration.
      </Alert>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Assessments
              </Typography>
              <Typography variant="h4">{stats.totalAssessments}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Resumes
              </Typography>
              <Typography variant="h4">{stats.totalResumes}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>User</TableCell>
                <TableCell>Date</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {assessments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No assessments found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                assessments.map((assessment) => (
                  <TableRow key={assessment.id}>
                    <TableCell>{assessment.id}</TableCell>
                    <TableCell>
                      {assessment.user?.email || assessment.user_email || assessment.user || 'N/A'}
                    </TableCell>
                    <TableCell>
                      {assessment.created_at 
                        ? new Date(assessment.created_at).toLocaleDateString()
                        : assessment.date || 'N/A'}
                    </TableCell>
                    <TableCell>{assessment.status || 'N/A'}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Container>
  );
};

export default AssessmentPage;
