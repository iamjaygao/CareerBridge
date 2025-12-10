import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
  Alert,
  Grid,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Description as DescriptionIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';

interface ResumeAnalysis {
  id: number;
  title: string;
  uploaded_at: string;
  status: 'uploaded' | 'analyzing' | 'analyzed' | 'failed';
  overall_score?: number;
}

const StudentAssessmentPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [analyses, setAnalyses] = useState<ResumeAnalysis[]>([]);
  const [lastAnalysis, setLastAnalysis] = useState<ResumeAnalysis | null>(null);

  useEffect(() => {
    setTimeout(() => {
      setAnalyses([
        {
          id: 1,
          title: 'Resume_2025.pdf',
          uploaded_at: '2025-01-15T10:00:00Z',
          status: 'analyzed',
          overall_score: 85,
        },
        {
          id: 2,
          title: 'Resume_Updated.pdf',
          uploaded_at: '2025-01-10T14:30:00Z',
          status: 'analyzed',
          overall_score: 78,
        },
      ]);
      setLastAnalysis({
        id: 1,
        title: 'Resume_2025.pdf',
        uploaded_at: '2025-01-15T10:00:00Z',
        status: 'analyzed',
        overall_score: 85,
      });
      setLoading(false);
    }, 500);
  }, []);

  const handleUpload = () => {
    // Placeholder for upload functionality
    alert('Upload functionality will be implemented');
  };

  if (loading) {
    return <LoadingSpinner message="Loading assessment data..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Resume Assessment
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Upload your resume and get AI-powered analysis
        </Typography>
      </Box>

      {/* Upload Section */}
      <Card sx={{ mb: 4 }}>
        <CardContent sx={{ p: 4, textAlign: 'center' }}>
          <UploadIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
          <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
            Upload Your Resume
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Get instant feedback on your resume with AI-powered analysis
          </Typography>
          <Button
            variant="contained"
            size="large"
            startIcon={<UploadIcon />}
            onClick={handleUpload}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
              },
            }}
          >
            Upload Resume
          </Button>
        </CardContent>
      </Card>

      {/* Last Analysis Result */}
      {lastAnalysis && lastAnalysis.status === 'analyzed' && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 3 }}>
              Last Analysis Result
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h3" sx={{ fontWeight: 700, color: 'primary.main' }}>
                    {lastAnalysis.overall_score}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Overall Score
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Structure Score
                  </Typography>
                  <LinearProgress variant="determinate" value={90} sx={{ height: 8, borderRadius: 4 }} />
                  <Typography variant="caption" color="text.secondary">
                    90/100
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Content Score
                  </Typography>
                  <LinearProgress variant="determinate" value={85} color="secondary" sx={{ height: 8, borderRadius: 4 }} />
                  <Typography variant="caption" color="text.secondary">
                    85/100
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    ATS Score
                  </Typography>
                  <LinearProgress variant="determinate" value={80} color="success" sx={{ height: 8, borderRadius: 4 }} />
                  <Typography variant="caption" color="text.secondary">
                    80/100
                  </Typography>
                </Box>
              </Grid>
            </Grid>
            <Alert severity="info" sx={{ mt: 3 }}>
              <Typography variant="body2">
                <strong>Key Insights:</strong> Your resume has strong structure and content. 
                Consider adding more industry-specific keywords to improve ATS compatibility.
              </Typography>
            </Alert>
          </CardContent>
        </Card>
      )}

      {/* History Table */}
      <Card>
        <CardContent>
          <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
            Upload History
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Resume</TableCell>
                  <TableCell>Uploaded</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Score</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {analyses.map((analysis) => (
                  <TableRow key={analysis.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <DescriptionIcon sx={{ mr: 1, color: 'text.secondary' }} />
                        <Typography variant="body2" fontWeight="medium">
                          {analysis.title}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      {new Date(analysis.uploaded_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={analysis.status.charAt(0).toUpperCase() + analysis.status.slice(1)}
                        color={analysis.status === 'analyzed' ? 'success' : analysis.status === 'analyzing' ? 'warning' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {analysis.overall_score ? (
                        <Typography variant="body2" fontWeight="medium">
                          {analysis.overall_score}/100
                        </Typography>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          -
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Button size="small" variant="outlined">
                        View Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default StudentAssessmentPage;

