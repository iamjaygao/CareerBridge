import React, { useEffect, useState } from 'react';
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
import adminService from '../../services/api/adminService';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const StaffResumesPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
          adminService.getAssessments({ limit: 20 }),
        ]);

        setStats({
          totalAssessments: statsData.total_assessments || statsData.totalAssessments || 0,
          totalResumes: statsData.total_resumes || statsData.totalResumes || 0,
        });

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
        const errorMessage = err?.response?.data?.detail
          || err?.response?.data?.error
          || err?.message
          || 'Failed to load resume reviews';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchAssessmentData();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading resume reviews..." />;
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
          Resume Reviews
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Review AI resume assessments and monitor analysis throughput.
        </Typography>
      </Box>

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
                <TableCell>Resume</TableCell>
                <TableCell>Score</TableCell>
                <TableCell>Date</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {assessments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No resume reviews found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                assessments.map((assessment) => (
                  <TableRow key={assessment.id}>
                    <TableCell>{assessment.id}</TableCell>
                    <TableCell>{assessment.resume_title || 'N/A'}</TableCell>
                    <TableCell>{assessment.overall_score ?? 'N/A'}</TableCell>
                    <TableCell>
                      {assessment.created_at
                        ? new Date(assessment.created_at).toLocaleDateString()
                        : 'N/A'}
                    </TableCell>
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

export default StaffResumesPage;
