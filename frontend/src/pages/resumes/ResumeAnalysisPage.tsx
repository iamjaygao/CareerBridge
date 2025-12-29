import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  Container,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Chip,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Rating,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  ArrowBack as ArrowBackIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import resumeService from '../../services/api/resumeService';
import { RootState } from '../../store';
import { getLandingPathByRole } from '../../utils/roleLanding';

interface AnalysisResult {
  id: number;
  resume: {
    id: number;
    title: string;
    file: string;
  };
  overall_score: number;
  structure_score: number;
  content_score: number;
  keyword_score: number;
  ats_score: number;
  extracted_text: string;
  detected_keywords: string[];
  missing_keywords: string[];
  industry_keywords: string[];
  technical_skills: string[];
  soft_skills: string[];
  skill_gaps: string[];
  experience_years: number;
  job_titles: string[];
  companies: string[];
  education_level: string;
  institutions: string[];
  certifications: string[];
  analysis_version: string;
  processing_time: number;
  confidence_score: number;
  score_category: string;
  created_at: string;
}

interface FeedbackResult {
  id: number;
  analysis: AnalysisResult;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  structure_recommendations: string[];
  content_recommendations: string[];
  industry_insights: string[];
  market_trends: string[];
  salary_insights: string;
  priority_actions: string[];
  quick_fixes: string[];
  long_term_improvements: string[];
}

const ResumeAnalysisPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [feedback, setFeedback] = useState<FeedbackResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const isStudent = user?.role === 'student';
  const basePath = isStudent ? '/student/resumes' : '/resumes';
  const dashboardPath = getLandingPathByRole(user?.role);
  const mentorsPath = isStudent ? '/student/mentors' : '/mentors';

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        setLoading(true);
        const analysisData = await resumeService.getAnalysis(parseInt(id!));
        setAnalysis(analysisData);
        
        // Fetch feedback if available
        try {
          const feedbackData = await resumeService.getFeedback(parseInt(id!));
          setFeedback(feedbackData);
        } catch (feedbackError) {
          console.log('No feedback available yet');
        }
      } catch (err) {
        setError('Failed to load analysis results');
        console.error('Analysis fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchAnalysis();
    }
  }, [id]);

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const handleDownload = async () => {
    if (!analysis) return;
    try {
      setDownloadError(null);
      const blob = await resumeService.downloadResume(analysis.resume.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${analysis.resume.title || 'resume'}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setDownloadError('Failed to download resume');
    }
  };

  const getScoreLabel = (score: number) => {
    if (score >= 90) return 'Excellent';
    if (score >= 80) return 'Very Good';
    if (score >= 70) return 'Good';
    if (score >= 60) return 'Fair';
    return 'Needs Improvement';
  };

  if (loading) {
    return <LoadingSpinner message="Loading analysis results..." />;
  }

  if (error || !analysis) {
    return <ErrorAlert message={error || 'Analysis not found'} />;
  }

  return (
    <>
      <PageHeader
        title={`Analysis: ${analysis.resume.title}`}
        breadcrumbs={[
          { label: 'Dashboard', path: dashboardPath },
          { label: 'Resumes', path: basePath },
          { label: 'Analysis', path: `${basePath}/${analysis.resume.id}/analysis` },
        ]}
      />

      <Container maxWidth="lg">
        <Box sx={{ mb: 3 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate(basePath)}
            sx={{ mb: 2 }}
          >
            Back to Resumes
          </Button>
          {downloadError && <ErrorAlert message={downloadError} />}
        </Box>

        {/* Overall Score Card */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <AssessmentIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h5" component="h2">
                Overall Analysis Score
              </Typography>
            </Box>
            
            <Grid container spacing={3} alignItems="center">
              <Grid item xs={12} md={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h2" color={`${getScoreColor(analysis.overall_score)}.main`}>
                    {analysis.overall_score}
                  </Typography>
                  <Typography variant="h6" color="text.secondary">
                    {getScoreLabel(analysis.overall_score)}
                  </Typography>
                  <Rating 
                    value={analysis.overall_score / 20} 
                    readOnly 
                    precision={0.5}
                    sx={{ mt: 1 }}
                  />
                </Box>
              </Grid>
              
              <Grid item xs={12} md={8}>
                <Typography variant="body1" paragraph>
                  Your resume has been analyzed using AI-powered tools to evaluate its effectiveness 
                  for job applications. Here's how it performed across different criteria.
                </Typography>
                
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Chip 
                    label={`Structure: ${analysis.structure_score}%`}
                    color={getScoreColor(analysis.structure_score)}
                    variant="outlined"
                  />
                  <Chip 
                    label={`Content: ${analysis.content_score}%`}
                    color={getScoreColor(analysis.content_score)}
                    variant="outlined"
                  />
                  <Chip 
                    label={`Keywords: ${analysis.keyword_score}%`}
                    color={getScoreColor(analysis.keyword_score)}
                    variant="outlined"
                  />
                  <Chip 
                    label={`ATS: ${analysis.ats_score}%`}
                    color={getScoreColor(analysis.ats_score)}
                    variant="outlined"
                  />
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        <Grid container spacing={3}>
          {/* Skills Analysis */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <CheckCircleIcon sx={{ mr: 1, color: 'success.main' }} />
                  Detected Skills
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  {analysis.technical_skills.map((skill, index) => (
                    <Chip key={index} label={skill} color="success" size="small" />
                  ))}
                  {analysis.soft_skills.map((skill, index) => (
                    <Chip key={index} label={skill} color="primary" size="small" />
                  ))}
                </Box>
                
                <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                  <WarningIcon sx={{ mr: 1, color: 'warning.main' }} />
                  Missing Skills
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {analysis.skill_gaps.map((skill, index) => (
                    <Chip key={index} label={skill} color="warning" variant="outlined" size="small" />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Keywords Analysis */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <TrendingUpIcon sx={{ mr: 1, color: 'success.main' }} />
                  Keyword Analysis
                </Typography>
                
                <Typography variant="subtitle2" gutterBottom>
                  Detected Keywords ({analysis.detected_keywords.length})
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  {analysis.detected_keywords.slice(0, 10).map((keyword, index) => (
                    <Chip key={index} label={keyword} color="success" size="small" />
                  ))}
                </Box>
                
                <Typography variant="subtitle2" gutterBottom>
                  Missing Keywords ({analysis.missing_keywords.length})
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {analysis.missing_keywords.slice(0, 10).map((keyword, index) => (
                    <Chip key={index} label={keyword} color="error" variant="outlined" size="small" />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Experience & Education */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Experience Summary
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText 
                      primary={`${analysis.experience_years} years of experience`}
                      secondary="Total professional experience"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary={analysis.job_titles.join(', ')}
                      secondary="Detected job titles"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary={analysis.companies.join(', ')}
                      secondary="Companies worked at"
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Education & Certifications
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText 
                      primary={analysis.education_level}
                      secondary="Education level"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary={analysis.institutions.join(', ')}
                      secondary="Educational institutions"
                    />
                  </ListItem>
                  {analysis.certifications.length > 0 && (
                    <ListItem>
                      <ListItemText 
                        primary={analysis.certifications.join(', ')}
                        secondary="Certifications"
                      />
                    </ListItem>
                  )}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Feedback Section */}
        {feedback && (
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                AI Feedback & Recommendations
              </Typography>
              
              <Accordion defaultExpanded>
                <AccordionSummary>
                  <Typography variant="h6">Summary</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body1">{feedback.summary}</Typography>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary>
                  <Typography variant="h6">Strengths</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List dense>
                    {feedback.strengths.map((strength, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <CheckCircleIcon color="success" />
                        </ListItemIcon>
                        <ListItemText primary={strength} />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary>
                  <Typography variant="h6">Areas for Improvement</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List dense>
                    {feedback.weaknesses.map((weakness, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <WarningIcon color="warning" />
                        </ListItemIcon>
                        <ListItemText primary={weakness} />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary>
                  <Typography variant="h6">Quick Fixes</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List dense>
                    {feedback.quick_fixes.map((fix, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <EditIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText primary={fix} />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary>
                  <Typography variant="h6">Long-term Improvements</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List dense>
                    {feedback.long_term_improvements.map((improvement, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <TrendingUpIcon color="success" />
                        </ListItemIcon>
                        <ListItemText primary={improvement} />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, mt: 3, justifyContent: 'center' }}>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={handleDownload}
          >
            Download Resume
          </Button>
          <Button
            variant="outlined"
            startIcon={<ShareIcon />}
            onClick={() => navigate(mentorsPath)}
          >
            Get Mentor Help
          </Button>
          <Button
            variant="outlined"
            onClick={() => navigate(basePath)}
          >
            Back to Resumes
          </Button>
        </Box>
      </Container>
    </>
  );
};

export default ResumeAnalysisPage; 
