import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  LinearProgress,
  Avatar,
  Chip,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Assessment as AssessmentIcon,
  Insights as InsightsIcon,
  Event as EventIcon,
  ArrowForward as ArrowForwardIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import mentorService from '../../services/api/mentorService';
import resumeService, { Resume } from '../../services/api/resumeService';
import appointmentService from '../../services/api/appointmentService';
import { Mentor } from '../../types';

const StudentDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState({
    assessment: 0,
    insights: 0,
    appointments: 0,
  });
  const [recommendedMentors, setRecommendedMentors] = useState<Mentor[]>([]);
  const [latestResume, setLatestResume] = useState<Resume | null>(null);
  const [actionItems, setActionItems] = useState({
    needsResume: false,
    needsReview: 0,
    upcomingAppointments: 0,
  });

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [mentorResponse, resumes, upcomingAppointments, completedAppointments] = await Promise.all([
          mentorService.getMentors({ page: 1, limit: 3 }),
          resumeService.getResumes(),
          appointmentService.getMyAppointments({ upcoming: 'true' }),
          appointmentService.getMyAppointments({ status: 'completed' }),
        ]);

        const mentorResults = mentorResponse?.results ?? mentorResponse ?? [];
        setRecommendedMentors(mentorResults.slice(0, 3));

        const latest = resumes?.[0] ?? null;
        setLatestResume(latest);

        const resumeStatus = latest?.status ?? null;
        let assessment = 0;
        let insights = 0;

        if (resumeStatus === 'uploaded') {
          assessment = 30;
          insights = 0;
        } else if (resumeStatus === 'analyzing') {
          assessment = 60;
          insights = 30;
        } else if (resumeStatus === 'analyzed') {
          assessment = 100;
          insights = 100;
        }

        const upcomingCount = Array.isArray(upcomingAppointments) ? upcomingAppointments.length : 0;
        const completedList = Array.isArray(completedAppointments) ? completedAppointments : [];
        const needsReview = completedList.filter(
          (appointment: any) => !appointment.user_rating && !appointment.user_feedback
        ).length;
        const needsResume = !latest || resumeStatus !== 'analyzed';

        setProgress({
          assessment,
          insights,
          appointments: upcomingCount,
        });
        setActionItems({
          needsResume,
          needsReview,
          upcomingAppointments: upcomingCount,
        });
      } catch {
        setProgress((prev) => ({ ...prev, appointments: 0 }));
        setRecommendedMentors([]);
        setLatestResume(null);
        setActionItems({
          needsResume: false,
          needsReview: 0,
          upcomingAppointments: 0,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading dashboard..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Welcome back!
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Continue your career journey
        </Typography>
      </Box>

      {/* Your Next Step Card */}
      <Card sx={{ mb: 4, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
                Your Next Step
              </Typography>
              <Typography variant="body1" sx={{ opacity: 0.9, mb: 2 }}>
                {latestResume
                  ? 'Update your resume to refresh insights and recommendations'
                  : 'Upload your resume to get personalized career insights and recommendations'}
              </Typography>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<UploadIcon />}
                  onClick={() => navigate('/student/assessment')}
                  sx={{
                    bgcolor: 'white',
                    color: 'primary.main',
                    '&:hover': {
                      bgcolor: 'grey.100',
                    },
                  }}
                >
                  {latestResume ? 'Update Resume' : 'Upload Resume'}
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/student/assessment')}
                  sx={{
                    borderColor: 'white',
                    color: 'white',
                    '&:hover': {
                      borderColor: 'white',
                      bgcolor: 'rgba(255,255,255,0.1)',
                    },
                  }}
                >
                  {latestResume ? 'Continue Analysis' : 'Start Analysis'}
                </Button>
              </Box>
            </Box>
            <AssessmentIcon sx={{ fontSize: 80, opacity: 0.3 }} />
          </Box>
        </CardContent>
      </Card>

      {/* Progress Summary */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AssessmentIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Assessment
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {progress.assessment}% Complete
                  </Typography>
                </Box>
              </Box>
              <LinearProgress
                variant="determinate"
                value={progress.assessment}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <InsightsIcon sx={{ fontSize: 40, color: 'secondary.main', mr: 2 }} />
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Insights
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {progress.insights}% Complete
                  </Typography>
                </Box>
              </Box>
              <LinearProgress
                variant="determinate"
                value={progress.insights}
                color="secondary"
                sx={{ height: 8, borderRadius: 4 }}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <EventIcon sx={{ fontSize: 40, color: 'success.main', mr: 2 }} />
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Appointments
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {progress.appointments} Upcoming
                  </Typography>
                </Box>
              </Box>
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate('/student/appointments')}
                sx={{ mt: 1 }}
              >
                View All
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Action Items */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
            Action Items
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    Resume & Insights
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {actionItems.needsResume ? 'Finish your assessment' : 'Insights are ready'}
                  </Typography>
                </Box>
                <Chip
                  label={actionItems.needsResume ? 'Pending' : 'Complete'}
                  color={actionItems.needsResume ? 'warning' : 'success'}
                  size="small"
                />
              </Box>
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate('/student/assessment')}
              >
                {actionItems.needsResume ? 'Complete Assessment' : 'View Insights'}
              </Button>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    Pending Reviews
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Completed sessions awaiting feedback
                  </Typography>
                </Box>
                <Chip label={actionItems.needsReview} color="info" size="small" />
              </Box>
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate('/student/appointments?tab=past&filter=needs_review')}
              >
                Leave Feedback
              </Button>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    Upcoming Sessions
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Upcoming appointments
                  </Typography>
                </Box>
                <Chip label={actionItems.upcomingAppointments} color="success" size="small" />
              </Box>
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate('/student/appointments?tab=upcoming')}
              >
                View Schedule
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Recommended Mentors */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            Recommended Mentors
          </Typography>
          <Button
            variant="text"
            endIcon={<ArrowForwardIcon />}
            onClick={() => navigate('/student/mentors')}
          >
            View All
          </Button>
        </Box>
        <Grid container spacing={3}>
          {recommendedMentors.map((mentor) => (
            <Grid item xs={12} sm={6} md={4} key={mentor.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ width: 56, height: 56, mr: 2, bgcolor: 'primary.main' }}>
                      {(mentor.display_name || mentor.user?.first_name || 'M').charAt(0)}
                    </Avatar>
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {mentor.display_name || mentor.user?.first_name || mentor.user?.username || 'Mentor'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {mentor.headline || mentor.job_title || mentor.industry || 'Career Mentor'}
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 0.5, mb: 2, flexWrap: 'wrap' }}>
                    {(mentor.expertise || []).slice(0, 2).map((tag) => (
                      <Chip key={tag} label={tag} size="small" />
                    ))}
                  </Box>
                  <Button
                    variant="contained"
                    fullWidth
                    onClick={() => navigate(`/student/mentors/${mentor.id}`)}
                    sx={{
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
                      },
                    }}
                  >
                    Book Session
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Market Highlights */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
            Market Highlights
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckCircleIcon sx={{ color: 'success.main', mr: 1 }} />
                <Typography variant="body2">
                  Software Engineer roles up 15% this month
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckCircleIcon sx={{ color: 'success.main', mr: 1 }} />
                <Typography variant="body2">
                  AI/ML skills in high demand
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckCircleIcon sx={{ color: 'success.main', mr: 1 }} />
                <Typography variant="body2">
                  Remote work opportunities increasing
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* CTA */}
      <Card sx={{ background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)' }}>
        <CardContent sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
            Continue Your Journey
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Explore market intelligence, book mentor sessions, and track your career progress
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              onClick={() => navigate('/student/intelligence')}
              sx={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
                },
              }}
            >
              Explore Market Intelligence
            </Button>
            <Button
              variant="outlined"
              onClick={() => navigate('/student/mentors')}
            >
              Find a Mentor
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default StudentDashboardPage;
