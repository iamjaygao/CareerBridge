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
  Paper,
  Grid,
  Pagination,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Assessment as AnalyzeIcon,
  Visibility as ViewIcon,
  Description as DescriptionIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { AppDispatch, RootState } from '../../store';
import { fetchResumes, deleteResume, analyzeResume } from '../../store/slices/resumeSlice';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import RegistrationBanner from '../../components/common/RegistrationBanner';
import UploadResumeDialog from '../../components/resumes/UploadResumeDialog';
import resumeService from '../../services/api/resumeService';
import ConsentDialog from '../../components/resumes/ConsentDialog';
import MissingConsentDialog from '../../components/resumes/MissingConsentDialog';
import { useNavigate } from 'react-router-dom';
import { createApiError } from '../../services/utils/errorHandler';

const ResumeListPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { resumes, loading, error } = useSelector((state: RootState) => state.resumes);
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);
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
  const [consentDialogOpen, setConsentDialogOpen] = useState(false);
  const [missingConsentDialogOpen, setMissingConsentDialogOpen] = useState(false);
  const [missingConsents, setMissingConsents] = useState<any[]>([]);
  const [missingConsentResumeId, setMissingConsentResumeId] = useState<number | null>(null);
  const [missingConsentError, setMissingConsentError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    // Only fetch resumes if user is authenticated
    // For unauthenticated users, show the introduction content only
    if (isAuthenticated) {
      dispatch(fetchResumes());
    }
  }, [dispatch, isAuthenticated]);

  const basePath = user?.role === 'student' ? '/student/resumes' : '/resumes';

  const handleUpload = () => {
    if (!isAuthenticated) {
      navigate('/login', { state: { redirectTo: basePath } });
      return;
    }
    setUploadDialogOpen(true);
  };

  const resumeBenefits = [
    'AI-powered resume analysis with instant feedback',
    'Get personalized suggestions to improve your resume',
    'Match your resume with relevant job opportunities',
    'Track your resume performance and optimization progress',
    'Access professional resume templates and examples',
  ];

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

  const startAnalysis = async (resumeId: number) => {
    setAnalysisResumeId(resumeId);
    setAnalysisDialogOpen(true);
    setAnalysisLoading(true);
    setAnalysisResult(null);
    setAnalysisError(null);
    try {
      // 1. 触发分析
      await resumeService.analyzeResume(resumeId, undefined, undefined, true, '1.0');
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
      const errorData = error?.response?.data;
      if (error?.response?.status === 403 && errorData?.required_disclaimers) {
        await handleMissingConsent(resumeId, errorData.required_disclaimers);
        setAnalysisDialogOpen(false);
        return;
      }
      setAnalysisError(error?.message || 'Failed to analyze resume');
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleAnalyze = (resumeId: number) => {
    setAnalysisResumeId(resumeId);
    setConsentDialogOpen(true);
  };

  const handleConsentConfirm = async () => {
    if (!analysisResumeId) return;
    setConsentDialogOpen(false);
    await startAnalysis(analysisResumeId);
  };

  const handleMissingConsent = async (resumeId: number, requiredDisclaimers: any[]) => {
    setMissingConsentResumeId(resumeId);
    setMissingConsentError(null);
    try {
      const details = await Promise.all(
        requiredDisclaimers.map((item) =>
          resumeService.getLegalDisclaimer(item.type || item.disclaimer_type)
        )
      );
      setMissingConsents(details);
    } catch (err: any) {
      setMissingConsents(requiredDisclaimers || []);
      setMissingConsentError(err?.message || 'Failed to load consent details.');
    }
    setMissingConsentDialogOpen(true);
  };

  const handleMissingConsentConfirm = async () => {
    if (!missingConsentResumeId) return;
    const disclaimerTypes = missingConsents.map((item) => item.disclaimer_type).filter(Boolean);
    try {
      await resumeService.grantConsent({
        consent_type: 'data_processing',
        consent_version: '1.0',
        disclaimer_types: disclaimerTypes,
      });
      setMissingConsentDialogOpen(false);
      await startAnalysis(missingConsentResumeId);
    } catch (err: any) {
      setMissingConsentError(err?.message || 'Failed to record consent.');
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

  // For unauthenticated users, don't show loading or error states
  // They should see the introduction content
  if (isAuthenticated) {
    if (loading) {
      return <LoadingSpinner message="Loading resumes..." />;
    }

    if (error) {
      return <ErrorAlert error={createApiError(error)} />;
    }
  }

  return (
    <>
      <PageHeader
        title="AI Resume Analysis"
        breadcrumbs={[{ label: 'Resumes', path: basePath }]}
        action={
          isAuthenticated && (
            <Button
              variant="contained"
              startIcon={<UploadIcon />}
              onClick={handleUpload}
            >
              Upload Resume
            </Button>
          )
        }
      />

      {!isAuthenticated && (
        <RegistrationBanner
          title="Unlock AI-Powered Resume Analysis"
          description="Sign up for free to upload your resume, get instant AI-powered feedback, and match with the perfect job opportunities."
        />
      )}

      {!isAuthenticated && (
        <Paper sx={{ p: 4, mb: 4, background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <DescriptionIcon sx={{ fontSize: 48, color: 'primary.main', mr: 2 }} />
            <Box>
              <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
                AI-Powered Resume Analysis
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Get instant feedback and improve your resume with AI technology
              </Typography>
            </Box>
          </Box>
          <Grid container spacing={2}>
            {resumeBenefits.map((benefit, index) => (
              <Grid item xs={12} sm={6} key={index}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                  <CheckCircleIcon sx={{ color: 'success.main', mr: 1, mt: 0.5 }} />
                  <Typography variant="body2">{benefit}</Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {isAuthenticated && (
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
                  Uploaded: {new Date((resume as any).uploaded_at || resume.created_at).toLocaleDateString()}
                </Typography>

                <Typography variant="body2" color="text.secondary">
                  File: {(resume as any).file_type ? (resume as any).file_type.toUpperCase() : 'PDF'} ({(resume as any).file_size || 0} bytes)
                </Typography>

                {((resume as any).analysis_result || resume.analysis) && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Analysis Results:
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Skills: {((resume as any).analysis_result?.technical_skills || (resume as any).analysis_result?.skills || resume.analysis?.technical_skills || resume.analysis?.skills || []).join(', ')}
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
                    onClick={() => navigate(`${basePath}/${resume.id}/analysis`)}
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
      )}

      {isAuthenticated && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination page={page} onChange={(_: React.ChangeEvent<unknown>, p: number) => setPage(p)} count={10} color="primary" />
        </Box>
      )}

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

      <ConsentDialog
        open={consentDialogOpen}
        onClose={() => setConsentDialogOpen(false)}
        onConfirm={handleConsentConfirm}
      />

      <MissingConsentDialog
        open={missingConsentDialogOpen}
        onClose={() => setMissingConsentDialogOpen(false)}
        onConfirm={handleMissingConsentConfirm}
        items={missingConsents}
        error={missingConsentError}
      />

      {/* AI分析结果弹窗 */}
      <Dialog open={analysisDialogOpen} onClose={() => setAnalysisDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>AI Resume Analysis Result</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            AI analysis is informational only and does not guarantee job outcomes.
          </Alert>
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
