import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingUpIcon,
  Work as WorkIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import resumeService, { Resume } from '../../services/api/resumeService';

interface ResumeAnalysis {
  overall_score?: number;
  structure_score?: number;
  content_score?: number;
  keyword_score?: number;
  ats_score?: number;
  detected_keywords?: string[];
  missing_keywords?: string[];
  industry_keywords?: string[];
  technical_skills?: string[];
  soft_skills?: string[];
  skill_gaps?: string[];
  experience_years?: number;
  job_titles?: string[];
}

interface ResumeFeedback {
  summary?: string;
  strengths?: string[];
  weaknesses?: string[];
  priority_actions?: string[];
  quick_fixes?: string[];
  long_term_improvements?: string[];
  structure_recommendations?: string[];
  content_recommendations?: string[];
  keyword_recommendations?: string[];
}

const StudentInsightsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null);
  const [feedback, setFeedback] = useState<ResumeFeedback | null>(null);
  const [resumeTitle, setResumeTitle] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [emptyState, setEmptyState] = useState(false);

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        const resumes = await resumeService.getResumes();
        const analyzed = resumes.filter((resume) => resume.status === 'analyzed');
        if (!analyzed.length) {
          setEmptyState(true);
          setAnalysis(null);
          setFeedback(null);
          setResumeTitle('');
          return;
        }

        const sorted = [...analyzed].sort((a: Resume, b: Resume) => {
          const dateA = new Date(a.analyzed_at || a.created_at || 0).getTime();
          const dateB = new Date(b.analyzed_at || b.created_at || 0).getTime();
          return dateB - dateA;
        });
        const latest = sorted[0];
        setResumeTitle(latest.title || 'Resume');

        const [analysisResult, feedbackResult] = await Promise.allSettled([
          resumeService.getResumeAnalysis(latest.id),
          resumeService.getFeedback(latest.id),
        ]);

        if (analysisResult.status === 'fulfilled') {
          setAnalysis(analysisResult.value || null);
        } else {
          setAnalysis(null);
        }

        if (feedbackResult.status === 'fulfilled') {
          setFeedback(feedbackResult.value || null);
        } else {
          setFeedback(null);
        }
      } catch {
        setError('Failed to load insights. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchInsights();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading insights..." />;
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (emptyState) {
    return (
      <Box>
        <Alert severity="info">
          Upload and analyze a resume to unlock personalized insights.
        </Alert>
      </Box>
    );
  }

  const strengths = feedback?.strengths?.length
    ? feedback.strengths
    : [
        ...(analysis?.technical_skills || []),
        ...(analysis?.soft_skills || []),
      ].slice(0, 3);

  const weaknesses = feedback?.weaknesses?.length
    ? feedback.weaknesses
    : (analysis?.skill_gaps?.length ? analysis.skill_gaps : analysis?.missing_keywords || []).slice(0, 3);

  const skillGaps = (analysis?.skill_gaps?.length ? analysis.skill_gaps : analysis?.missing_keywords || []).slice(0, 3);
  const recommendedRoles = analysis?.job_titles?.length ? analysis.job_titles : [];

  const experienceYears = analysis?.experience_years ?? 0;
  const currentLevel =
    experienceYears >= 8
      ? 'Staff or Lead-level Engineer'
      : experienceYears >= 5
        ? 'Senior-level Engineer'
        : experienceYears >= 2
          ? 'Mid-level Engineer'
          : 'Early-career Professional';

  const roadmapNextStep =
    feedback?.priority_actions?.[0] ||
    feedback?.quick_fixes?.[0] ||
    feedback?.structure_recommendations?.[0] ||
    'Focus on polishing your resume structure and clarity.';
  const roadmapYearStep =
    feedback?.content_recommendations?.[0] ||
    feedback?.keyword_recommendations?.[0] ||
    'Add measurable impact and role-specific keywords.';
  const roadmapLongTerm =
    feedback?.long_term_improvements?.[0] ||
    (recommendedRoles[0] ? `Prepare for ${recommendedRoles[0]} opportunities.` : 'Build a long-term growth plan.');

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Career Insights
        </Typography>
        <Typography variant="body2" color="text.secondary">
          AI-powered analysis based on {resumeTitle}
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Strengths */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <CheckCircleIcon sx={{ color: 'success.main', mr: 1, fontSize: 28 }} />
                <Typography variant="h5" sx={{ fontWeight: 700 }}>
                  Strengths
                </Typography>
              </Box>
              <List>
                {strengths.length ? (
                  strengths.map((item) => (
                    <ListItem key={item}>
                      <ListItemIcon>
                        <CheckCircleIcon color="success" />
                      </ListItemIcon>
                      <ListItemText
                        primary={item}
                        secondary="Highlighted by your resume analysis"
                      />
                    </ListItem>
                  ))
                ) : (
                  <ListItem>
                    <ListItemText
                      primary="No strength highlights yet"
                      secondary="Run resume analysis to generate insights."
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Weaknesses */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <WarningIcon sx={{ color: 'warning.main', mr: 1, fontSize: 28 }} />
                <Typography variant="h5" sx={{ fontWeight: 700 }}>
                  Areas for Improvement
                </Typography>
              </Box>
              <List>
                {weaknesses.length ? (
                  weaknesses.map((item) => (
                    <ListItem key={item}>
                      <ListItemIcon>
                        <WarningIcon color="warning" />
                      </ListItemIcon>
                      <ListItemText
                        primary={item}
                        secondary="Opportunity to strengthen this area"
                      />
                    </ListItem>
                  ))
                ) : (
                  <ListItem>
                    <ListItemText
                      primary="No improvement areas yet"
                      secondary="Run resume analysis to see recommendations."
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Skill Gaps */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                Skill Gaps
              </Typography>
              {skillGaps.length ? (
                skillGaps.map((gap, index) => {
                  const score = Math.max(25, 65 - index * 15);
                  const color = index === 0 ? 'error' : index === 1 ? 'warning' : 'primary';
                  return (
                    <Box key={gap} sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="body2">{gap}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {score}%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={score}
                        color={color as 'primary' | 'warning' | 'error'}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    </Box>
                  );
                })
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No skill gaps identified yet.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recommended Roles */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <WorkIcon sx={{ color: 'primary.main', mr: 1, fontSize: 28 }} />
                <Typography variant="h5" sx={{ fontWeight: 700 }}>
                  Recommended Roles
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                {recommendedRoles.length ? (
                  recommendedRoles.map((role) => (
                    <Box
                      key={role}
                      sx={{
                        p: 2,
                        border: '1px solid',
                        borderColor: 'divider',
                        borderRadius: 2,
                        '&:hover': {
                          bgcolor: 'grey.50',
                        },
                      }}
                    >
                      <Typography variant="body1" fontWeight="medium">
                        {role}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Suggested based on your resume analysis
                      </Typography>
                    </Box>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No role recommendations yet.
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Career Roadmap */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <TrendingUpIcon sx={{ color: 'primary.main', mr: 1, fontSize: 28 }} />
                <Typography variant="h5" sx={{ fontWeight: 700 }}>
                  Career Roadmap
                </Typography>
              </Box>
              <Box sx={{ position: 'relative', pl: 3 }}>
                {[
                  { title: 'Current Level', description: currentLevel, time: 'Now' },
                  { title: 'Next 6 Months', description: roadmapNextStep, time: '6 months' },
                  { title: 'Next 1 Year', description: roadmapYearStep, time: '1 year' },
                  { title: 'Long-term Goal', description: roadmapLongTerm, time: '2-3 years' },
                ].map((step, index) => (
                  <Box
                    key={index}
                    sx={{
                      position: 'relative',
                      pb: 3,
                      '&:not(:last-child)::before': {
                        content: '""',
                        position: 'absolute',
                        left: '-11px',
                        top: '24px',
                        bottom: '-12px',
                        width: '2px',
                        bgcolor: 'divider',
                      },
                    }}
                  >
                    <Box
                      sx={{
                        position: 'absolute',
                        left: '-15px',
                        top: '4px',
                        width: '12px',
                        height: '12px',
                        borderRadius: '50%',
                        bgcolor: 'primary.main',
                        border: '2px solid white',
                        boxShadow: '0 0 0 2px',
                      }}
                    />
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                      {step.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      {step.description}
                    </Typography>
                    <Chip label={step.time} size="small" />
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default StudentInsightsPage;
