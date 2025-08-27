import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Card,
  CardContent,
  CardActions,
  Button,
  Typography,
  Box,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Snackbar,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Grid } from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Assessment as AnalyzeIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { AppDispatch, RootState } from '../../store';
import { fetchResumes, deleteResume, analyzeResume } from '../../store/slices/resumeSlice';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import UploadResumeDialog from '../../components/resumes/UploadResumeDialog';
import resumeService from '../../services/api/resumeService';
import { useNavigate } from 'react-router-dom';

const ResumeListPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { resumes, loading, error } = useSelector((state: RootState) => state.resumes);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });
  const [analysisDialogOpen, setAnalysisDialogOpen] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisResumeId, setAnalysisResumeId] = useState<number | null>(null);

  useEffect(() => {
    dispatch(fetchResumes());
  }, [dispatch]);

  const handleUpload = () => {
    setUploadDialogOpen(true);
  };

  const handleDownload = async (resumeId: number) => {
    try {
      const blob = await resumeService.downloadResume(resumeId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `resume_${resumeId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to download resume',
        severity: 'error',
      });
    }
  };

  const handleAnalyze = async (resumeId: number) => {
    setAnalysisResumeId(resumeId);
    setAnalysisDialogOpen(true);
    setAnalysisLoading(true);
    setAnalysisResult(null);
    setAnalysisError(null);
    try {
      // 1. 触发分析
      await resumeService.analyzeResume(resumeId);
      // 2. 轮询获取分析结果
      let attempts = 0;
      let result = null;
      while (attempts < 10) {
        await new Promise((r) => setTimeout(r, 2000));
        result = await resumeService.getAnalysis(resumeId);
        if (result && result.overall_score) break;
        attempts++;
      }
      if (!result || !result.overall_score) {
        throw new Error('Analysis not completed. Please try again later.');
      }
      setAnalysisResult(result);
    } catch (error: any) {
      setAnalysisError(error?.message || 'Failed to analyze resume');
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleDelete = (resumeId: number) => {
    setSelectedResumeId(resumeId);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (selectedResumeId) {
      try {
        await dispatch(deleteResume(selectedResumeId)).unwrap();
        setSnackbar({
          open: true,
          message: 'Resume deleted successfully',
          severity: 'success',
        });
      } catch (error) {
        setSnackbar({
          open: true,
          message: 'Failed to delete resume',
          severity: 'error',
        });
      }
    }
    setDeleteDialogOpen(false);
    setSelectedResumeId(null);
  };

  if (loading) {
    return <LoadingSpinner message="Loading resumes..." />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  return (
    <>
      <PageHeader
        title="My Resumes"
        breadcrumbs={[{ label: 'Resumes', path: '/resumes' }]}
        action={
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={handleUpload}
          >
            Upload Resume
          </Button>
        }
      />

      <Grid container spacing={3}>
        {resumes.map((resume) => (
          <Grid item xs={12} sm={6} md={4} key={resume.id}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                },
              }}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                    {resume.title}
                  </Typography>
                  <Chip
                    label={resume.status}
                    color={
                      resume.status === 'analyzed'
                        ? 'success'
                        : resume.status === 'analyzing'
                        ? 'warning'
                        : resume.status === 'failed'
                        ? 'error'
                        : 'default'
                    }
                    size="small"
                  />
                </Box>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Uploaded: {new Date(resume.uploaded_at).toLocaleDateString()}
                </Typography>

                <Typography variant="body2" color="text.secondary">
                  File: {resume.file_type.toUpperCase()} ({resume.file_size} bytes)
                </Typography>

                {resume.analysis_result && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Analysis Results:
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Skills: {resume.analysis_result.skills.join(', ')}
                    </Typography>
                  </Box>
                )}
              </CardContent>

              <CardActions>
                <IconButton
                  size="small"
                  onClick={() => handleDownload(resume.id)}
                  title="Download"
                >
                  <DownloadIcon />
                </IconButton>
                {resume.status === 'analyzed' && (
                  <IconButton
                    size="small"
                    onClick={() => navigate(`/resumes/${resume.id}/analysis`)}
                    title="View Analysis"
                    color="primary"
                  >
                    <ViewIcon />
                  </IconButton>
                )}
                <IconButton
                  size="small"
                  onClick={() => handleAnalyze(resume.id)}
                  title="AI Analyze"
                  disabled={resume.status === 'analyzing'}
                  color="secondary"
                >
                  <AnalyzeIcon />
                </IconButton>
                <IconButton
                  size="small"
                  onClick={() => handleDelete(resume.id)}
                  title="Delete"
                  color="error"
                >
                  <DeleteIcon />
                </IconButton>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Upload Dialog */}
      <UploadResumeDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Resume</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this resume? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={confirmDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* AI分析结果弹窗 */}
      <Dialog open={analysisDialogOpen} onClose={() => setAnalysisDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>AI Resume Analysis Result</DialogTitle>
        <DialogContent>
          {analysisLoading ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
              <CircularProgress />
              <Typography variant="body2" sx={{ mt: 2 }}>
                Analyzing resume, please wait...
              </Typography>
            </Box>
          ) : analysisError ? (
            <Alert severity="error">{analysisError}</Alert>
          ) : analysisResult ? (
            <Box>
              <Typography variant="h6" gutterBottom>
                Overall Score: {analysisResult.overall_score}
              </Typography>
              <Typography variant="subtitle1">Strengths:</Typography>
              <ul>
                {analysisResult.strengths?.map((s: string, i: number) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
              <Typography variant="subtitle1">Weaknesses:</Typography>
              <ul>
                {analysisResult.weaknesses?.map((w: string, i: number) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
              <Typography variant="subtitle1">Suggestions:</Typography>
              <ul>
                {analysisResult.suggestions?.map((s: string, i: number) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
              <Typography variant="subtitle1">ATS Compatibility:</Typography>
              <ul>
                {analysisResult.ats_compatibility?.issues?.map((issue: string, i: number) => (
                  <li key={i}>{issue}</li>
                ))}
              </ul>
              <Typography variant="subtitle1">Technical Skills:</Typography>
              <ul>
                {analysisResult.skill_analysis?.technical_skills?.map((skill: string, i: number) => (
                  <li key={i}>{skill}</li>
                ))}
              </ul>
            </Box>
          ) : (
            <Typography>No analysis result available.</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAnalysisDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default ResumeListPage; 