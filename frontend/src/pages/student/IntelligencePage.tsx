import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Paper,
  Button,
  Alert,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Work as WorkIcon,
  Star as StarIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import resumeService, { Resume } from '../../services/api/resumeService';

interface ResumeAnalysis {
  job_titles?: string[];
  technical_skills?: string[];
  detected_keywords?: string[];
}

interface JobSummary {
  title: string;
  company?: string;
  location?: string;
  match?: number;
}

const StudentIntelligencePage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [emptyState, setEmptyState] = useState(false);
  const [resumeTitle, setResumeTitle] = useState<string>('');
  const [focusRole, setFocusRole] = useState<string>('Software Engineer');
  const [salaryValue, setSalaryValue] = useState<string | null>(null);
  const [salaryLocation, setSalaryLocation] = useState<string>('United States');
  const [trendLabel, setTrendLabel] = useState<string>('');
  const [trendValue, setTrendValue] = useState<string | null>(null);
  const [recommendedJobs, setRecommendedJobs] = useState<JobSummary[]>([]);
  const [skillsDemand, setSkillsDemand] = useState<string[]>([]);

  useEffect(() => {
    const fetchIntelligence = async () => {
      try {
        const resumes = await resumeService.getResumes();
        const analyzed = resumes.filter((resume) => resume.status === 'analyzed');
        if (!analyzed.length) {
          setEmptyState(true);
          return;
        }

        const sorted = [...analyzed].sort((a: Resume, b: Resume) => {
          const dateA = new Date(a.analyzed_at || a.created_at || 0).getTime();
          const dateB = new Date(b.analyzed_at || b.created_at || 0).getTime();
          return dateB - dateA;
        });

        const latest = sorted[0];
        setResumeTitle(latest.title || 'Resume');

        const analysis = await resumeService.getResumeAnalysis(latest.id);
        const analysisData: ResumeAnalysis = analysis || {};

        const primaryRole = analysisData.job_titles?.[0] || latest.title || 'Software Engineer';
        setFocusRole(primaryRole);

        const fallbackSkills = [
          ...(analysisData.technical_skills || []),
          ...(analysisData.detected_keywords || []),
        ].filter(Boolean);

        const [
          recommendationsResult,
          salaryResult,
          trendingResult,
          skillsResult,
        ] = await Promise.allSettled([
          resumeService.getJobRecommendations(latest.id, 3),
          resumeService.getSalaryData(primaryRole, salaryLocation),
          resumeService.getTrendingJobs(),
          resumeService.getSkillDemand(primaryRole, salaryLocation),
        ]);

        if (recommendationsResult.status === 'fulfilled') {
          const items = (recommendationsResult.value || []).map((job: any) => ({
            title: job.title || job.job_title || job.position || 'Role',
            company: job.company || job.company_name || job.employer,
            location: job.location || job.city || job.remote || 'Remote',
            match: job.match_score || job.match || job.score,
          }));
          setRecommendedJobs(items.filter((item) => item.title));
        }

        if (salaryResult.status === 'fulfilled') {
          const data = salaryResult.value || {};
          const rawValue =
            data.average_salary ||
            data.median_salary ||
            data.average ||
            data.median ||
            data.salary?.average ||
            data.salary?.median;
          if (rawValue) {
            const formatted = typeof rawValue === 'number'
              ? new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                  maximumFractionDigits: 0,
                }).format(rawValue)
              : String(rawValue);
            setSalaryValue(formatted);
          }
        }

        if (trendingResult.status === 'fulfilled') {
          const data = trendingResult.value || {};
          const items =
            data.jobs ||
            data.trending ||
            data.results ||
            data.data?.jobs ||
            [];
          const first = Array.isArray(items) ? items[0] : null;
          setTrendLabel(first?.title || first?.job_title || primaryRole);
          const rawTrend =
            data.trend_percentage ||
            data.growth ||
            data.change ||
            data.trend ||
            data.data?.trend_percentage;
          if (rawTrend !== undefined && rawTrend !== null) {
            const trendNumber = Number(rawTrend);
            if (!Number.isNaN(trendNumber)) {
              setTrendValue(`${trendNumber >= 0 ? '+' : ''}${trendNumber}%`);
            } else {
              setTrendValue(String(rawTrend));
            }
          } else if (Array.isArray(items)) {
            setTrendValue(`${items.length} roles trending`);
          }
        }

        if (skillsResult.status === 'fulfilled') {
          const data = skillsResult.value || {};
          const rawSkills =
            data.skills ||
            data.top_skills ||
            data.results ||
            data.data?.skills ||
            [];
          const normalized = Array.isArray(rawSkills)
            ? rawSkills.map((skill: any) => skill.name || skill.skill || skill).filter(Boolean)
            : [];
          setSkillsDemand(normalized.slice(0, 12));
        } else if (fallbackSkills.length) {
          setSkillsDemand(fallbackSkills.slice(0, 12));
        }
      } catch {
        setError('Failed to load market intelligence data.');
      } finally {
        setLoading(false);
      }
    };

    fetchIntelligence();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading market intelligence..." />;
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (emptyState) {
    return (
      <Box>
        <Alert severity="info">
          Upload and analyze a resume to unlock market intelligence.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Market Intelligence
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Insights personalized for {resumeTitle}
        </Typography>
      </Box>

      {/* Market Demand Charts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUpIcon sx={{ color: 'primary.main', mr: 1, fontSize: 28 }} />
                <Typography variant="h5" sx={{ fontWeight: 700 }}>
                  Market Demand Trends
                </Typography>
              </Box>
              <Paper
                variant="outlined"
                sx={{
                  p: 4,
                  textAlign: 'center',
                  bgcolor: 'grey.50',
                  minHeight: 250,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'success.main', mb: 1 }}>
                    {trendValue || '—'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {trendLabel || focusRole}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                    Recent market activity
                  </Typography>
                </Box>
              </Paper>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <WorkIcon sx={{ color: 'primary.main', mr: 1, fontSize: 28 }} />
                <Typography variant="h5" sx={{ fontWeight: 700 }}>
                  Salary Trends
                </Typography>
              </Box>
              <Paper
                variant="outlined"
                sx={{
                  p: 4,
                  textAlign: 'center',
                  bgcolor: 'grey.50',
                  minHeight: 250,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'info.main', mb: 1 }}>
                    {salaryValue || '—'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Average salary
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                    {focusRole} ({salaryLocation})
                  </Typography>
                </Box>
              </Paper>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recommended Jobs */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
          Recommended Jobs
        </Typography>
        <Grid container spacing={2}>
          {(recommendedJobs.length ? recommendedJobs : [{ title: focusRole, location: 'Remote' }]).map((job, index) => (
            <Grid item xs={12} md={4} key={`${job.title}-${index}`}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {job.title}
                    </Typography>
                    {job.match ? (
                      <Chip label={`${job.match}% match`} color="success" size="small" />
                    ) : null}
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {job.company || 'Suggested by your resume'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {job.location || 'Remote'}
                  </Typography>
                  <Button variant="outlined" fullWidth size="small">
                    View Details
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Skills in Demand */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <StarIcon sx={{ color: 'warning.main', mr: 1, fontSize: 28 }} />
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              Skills in Demand
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {skillsDemand.length ? (
              skillsDemand.map((skill) => (
                <Chip
                  key={skill}
                  label={skill}
                  color="primary"
                  variant="outlined"
                  sx={{ fontWeight: 500 }}
                />
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">
                No market skills available yet.
              </Typography>
            )}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default StudentIntelligencePage;
