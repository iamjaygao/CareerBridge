import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import resumeService from '../../services/api/resumeService';

interface ResumeAnalysisDetail {
  overall_score?: number;
  structure_score?: number;
  content_score?: number;
  keyword_score?: number;
  ats_score?: number;
  created_at?: string;
}

const ResumeAnalysisDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState<ResumeAnalysisDetail | null>(null);
  const [resumeTitle, setResumeTitle] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const resumeId = Number(id);
    if (!resumeId) {
      setError('Invalid resume ID');
      setLoading(false);
      return;
    }

    const fetchDetail = async () => {
      try {
        const [resumeResult, analysisResult] = await Promise.allSettled([
          resumeService.getResume(resumeId),
          resumeService.getResumeAnalysis(resumeId),
        ]);

        if (resumeResult.status === 'rejected') {
          throw resumeResult.reason;
        }

        setResumeTitle(resumeResult.value.title || 'Resume');

        if (analysisResult.status === 'fulfilled') {
          setAnalysis(analysisResult.value || null);
          return;
        }

        if (axios.isAxiosError(analysisResult.reason)) {
          const status = analysisResult.reason.response?.status;
          if (status === 404) {
            setAnalysis(null);
            return;
          }
        }

        throw analysisResult.reason;
      } catch {
        setError('Failed to load analysis details. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [id]);

  if (loading) {
    return <LoadingSpinner message="Loading analysis..." />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  if (!analysis) {
    return (
      <Box>
        <Alert severity="info">No analysis data available yet.</Alert>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/student/assessment')}
          sx={{ mt: 2 }}
        >
          Back to Assessments
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/student/assessment')}
          sx={{ mr: 2 }}
        >
          Back
        </Button>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            Resume Analysis
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {resumeTitle}
          </Typography>
        </Box>
      </Box>

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <DescriptionIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              Overall Score
            </Typography>
          </Box>
          <Typography variant="h3" sx={{ fontWeight: 700, color: 'primary.main' }}>
            {analysis.overall_score ?? '--'}
          </Typography>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                Structure Score
              </Typography>
              <LinearProgress
                variant="determinate"
                value={analysis.structure_score ?? 0}
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary">
                {analysis.structure_score ? `${analysis.structure_score}/100` : '--'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                Content Score
              </Typography>
              <LinearProgress
                variant="determinate"
                value={analysis.content_score ?? 0}
                color="secondary"
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary">
                {analysis.content_score ? `${analysis.content_score}/100` : '--'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                Keyword Score
              </Typography>
              <LinearProgress
                variant="determinate"
                value={analysis.keyword_score ?? 0}
                color="warning"
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary">
                {analysis.keyword_score ? `${analysis.keyword_score}/100` : '--'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                ATS Score
              </Typography>
              <LinearProgress
                variant="determinate"
                value={analysis.ats_score ?? 0}
                color="success"
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary">
                {analysis.ats_score ? `${analysis.ats_score}/100` : '--'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ResumeAnalysisDetailPage;
