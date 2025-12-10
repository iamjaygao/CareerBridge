import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Alert,
} from '@mui/material';
import { Assessment as AssessmentIcon, Delete as DeleteIcon, Edit as EditIcon } from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { useRole } from '../../contexts/RoleContext';
import adminService from '../../services/api/adminService';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const AssessmentPage: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const { isSuperAdmin } = useRole();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({
    totalAssessments: 0,
    totalResumes: 0,
    aiUsage: 0,
  });

  useEffect(() => {
    const fetchAssessmentStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await adminService.getAssessmentStats();
        
        setStats({
          totalAssessments: data.total_assessments || data.totalAssessments || 0,
          totalResumes: data.total_resumes || data.totalResumes || 0,
          aiUsage: data.ai_usage || data.aiUsage || data.ai_api_calls || 0,
        });
      } catch (err: any) {
        const errorMessage = err?.response?.data?.detail 
          || err?.response?.data?.error
          || err?.message 
          || 'Failed to load assessment statistics';
        setError(errorMessage);
        console.error('Failed to fetch assessment stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAssessmentStats();
  }, []);

  if (!isSuperAdmin) {
    return null;
  }

  if (loading) {
    return <LoadingSpinner message="Loading assessment statistics..." />;
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
          Assessment Engine Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage AI assessment system, prompts, and configuration
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Assessments
              </Typography>
              <Typography variant="h4">{stats.totalAssessments}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Resumes
              </Typography>
              <Typography variant="h4">{stats.totalResumes}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                AI API Calls
              </Typography>
              <Typography variant="h4">{stats.aiUsage}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Engine Configuration
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <Button variant="outlined" startIcon={<EditIcon />}>
            Edit Prompts
          </Button>
          <Button variant="outlined" startIcon={<EditIcon />}>
            Edit AI Config
          </Button>
          <Button variant="outlined" color="error" startIcon={<DeleteIcon />}>
            Reset Records
          </Button>
        </Box>
      </Paper>

      <Alert severity="info">
        SuperAdmin has full access to modify assessment engine prompts, AI configuration, and delete assessment records.
      </Alert>
    </Container>
  );
};

export default AssessmentPage;

