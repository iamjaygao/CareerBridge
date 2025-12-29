import React, { useState, useEffect, useRef } from 'react';
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
import resumeService, { Resume } from '../../services/api/resumeService';
import ConsentDialog from '../../components/resumes/ConsentDialog';
import MissingConsentDialog from '../../components/resumes/MissingConsentDialog';
import { useNavigate } from 'react-router-dom';
import { getUserFacingErrorMessage } from '../../services/utils/errorHandler';

interface ResumeSummary extends Resume {
  uploaded_at?: string;
}

interface AnalysisScores {
  overall_score?: number;
  structure_score?: number;
  content_score?: number;
  ats_score?: number;
}

const StudentAssessmentPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [analyses, setAnalyses] = useState<ResumeSummary[]>([]);
  const [lastAnalysis, setLastAnalysis] = useState<ResumeSummary | null>(null);
  const [lastScores, setLastScores] = useState<AnalysisScores | null>(null);
  const [uploading, setUploading] = useState(false);
  const [analyzingId, setAnalyzingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [consentDialogOpen, setConsentDialogOpen] = useState(false);
  const [pendingAnalysisId, setPendingAnalysisId] = useState<number | null>(null);
  const [missingConsentDialogOpen, setMissingConsentDialogOpen] = useState(false);
  const [missingConsents, setMissingConsents] = useState<any[]>([]);
  const [missingConsentResumeId, setMissingConsentResumeId] = useState<number | null>(null);
  const [missingConsentError, setMissingConsentError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const fetchResumes = async () => {
      try {
        const resumes = await resumeService.getResumes();
        const sorted = [...resumes].sort((a, b) => {
          const dateA = new Date((a as ResumeSummary).uploaded_at || a.created_at || 0).getTime();
          const dateB = new Date((b as ResumeSummary).uploaded_at || b.created_at || 0).getTime();
          return dateB - dateA;
        });
        setAnalyses(sorted);
        const latest = sorted[0] || null;
        setLastAnalysis(latest);

        if (latest && latest.status === 'analyzed') {
          try {
            const analysis = await resumeService.getResumeAnalysis(latest.id);
            setLastScores({
              overall_score: analysis.overall_score,
              structure_score: analysis.structure_score,
              content_score: analysis.content_score,
              ats_score: analysis.ats_score,
            });
          } catch {
            setLastScores(null);
          }
        } else {
          setLastScores(null);
        }
      } catch (err) {
        setError(getUserFacingErrorMessage(err, 'Failed to load resumes. Please try again.'));
        setAnalyses([]);
        setLastAnalysis(null);
        setLastScores(null);
      } finally {
        setLoading(false);
      }
    };

    fetchResumes();
  }, []);

  const handleUpload = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelected = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setUploading(true);
    setError(null);
    try {
      await resumeService.uploadResume(file, file.name);
      await refreshResumes();
    } catch (err) {
      setError(getUserFacingErrorMessage(err, 'Upload failed. Please try again.'));
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const refreshResumes = async () => {
    const resumes = await resumeService.getResumes();
    const sorted = [...resumes].sort((a, b) => {
      const dateA = new Date((a as ResumeSummary).uploaded_at || a.created_at || 0).getTime();
      const dateB = new Date((b as ResumeSummary).uploaded_at || b.created_at || 0).getTime();
      return dateB - dateA;
    });
    setAnalyses(sorted);
    setLastAnalysis(sorted[0] || null);
    if (sorted[0] && sorted[0].status === 'analyzed') {
      try {
        const analysis = await resumeService.getResumeAnalysis(sorted[0].id);
        setLastScores({
          overall_score: analysis.overall_score,
          structure_score: analysis.structure_score,
          content_score: analysis.content_score,
          ats_score: analysis.ats_score,
        });
      } catch {
        setLastScores(null);
      }
    } else {
      setLastScores(null);
    }
  };

  const startAnalysis = async (resumeId: number) => {
    setAnalyzingId(resumeId);
    setError(null);
    try {
      await resumeService.analyzeResume(resumeId, undefined, undefined, true, '1.0');
      await refreshResumes();
    } catch (err: any) {
      const errorData = err?.response?.data;
      if (err?.response?.status === 403 && errorData?.required_disclaimers) {
        await handleMissingConsent(resumeId, errorData.required_disclaimers);
        return;
      }
      setError(errorData?.error || getUserFacingErrorMessage(err, 'Analysis failed. Please try again later.'));
    } finally {
      setAnalyzingId(null);
    }
  };

  const handleAnalyze = (resumeId: number) => {
    setPendingAnalysisId(resumeId);
    setConsentDialogOpen(true);
  };

  const handleConsentConfirm = async () => {
    if (!pendingAnalysisId) return;
    setConsentDialogOpen(false);
    await startAnalysis(pendingAnalysisId);
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
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
        {lastAnalysis?.status === 'failed' && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            Your last analysis failed. You can retry the analysis from the table below.
          </Alert>
        )}
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
            disabled={uploading}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
              },
            }}
          >
            {uploading ? 'Uploading...' : 'Upload Resume'}
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.doc,.docx"
            onChange={handleFileSelected}
            style={{ display: 'none' }}
          />
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
                    {lastScores?.overall_score ?? '--'}
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
                  <LinearProgress
                    variant="determinate"
                    value={lastScores?.structure_score ?? 0}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {lastScores?.structure_score ? `${lastScores.structure_score}/100` : '--'}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Content Score
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={lastScores?.content_score ?? 0}
                    color="secondary"
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {lastScores?.content_score ? `${lastScores.content_score}/100` : '--'}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    ATS Score
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={lastScores?.ats_score ?? 0}
                    color="success"
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {lastScores?.ats_score ? `${lastScores.ats_score}/100` : '--'}
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
                      {new Date(analysis.uploaded_at || analysis.created_at || '').toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={analysis.status.charAt(0).toUpperCase() + analysis.status.slice(1)}
                        color={analysis.status === 'analyzed' ? 'success' : analysis.status === 'analyzing' ? 'warning' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {lastAnalysis?.id === analysis.id && lastScores?.overall_score ? (
                        <Typography variant="body2" fontWeight="medium">
                          {lastScores.overall_score}/100
                        </Typography>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          -
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => navigate(`/student/assessment/${analysis.id}`)}
                      >
                        View Details
                      </Button>
                      {(analysis.status === 'uploaded' || analysis.status === 'failed') && (
                        <Button
                          size="small"
                          variant="contained"
                          sx={{ ml: 1 }}
                          onClick={() => handleAnalyze(analysis.id)}
                          disabled={analyzingId === analysis.id}
                        >
                          {analysis.status === 'failed' ? 'Retry' : 'Analyze'}
                        </Button>
                      )}
                      {analysis.status === 'analyzing' && (
                        <Button size="small" variant="outlined" sx={{ ml: 1 }} disabled>
                          Analyzing...
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

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
    </Box>
  );
};

export default StudentAssessmentPage;
