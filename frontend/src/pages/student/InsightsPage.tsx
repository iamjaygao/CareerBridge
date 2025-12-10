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
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingUpIcon,
  Work as WorkIcon,
  School as SchoolIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const StudentInsightsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setLoading(false);
    }, 500);
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading insights..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Career Insights
        </Typography>
        <Typography variant="body2" color="text.secondary">
          AI-powered analysis of your career profile
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
                <ListItem>
                  <ListItemIcon>
                    <CheckCircleIcon color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Strong Technical Skills"
                    secondary="Proficient in multiple programming languages and frameworks"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircleIcon color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Problem-Solving Ability"
                    secondary="Demonstrated ability to tackle complex challenges"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircleIcon color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Communication Skills"
                    secondary="Clear and effective written and verbal communication"
                  />
                </ListItem>
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
                <ListItem>
                  <ListItemIcon>
                    <WarningIcon color="warning" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Industry Experience"
                    secondary="Consider gaining more hands-on experience in your target industry"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <WarningIcon color="warning" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Leadership Experience"
                    secondary="Opportunities to lead projects or teams would strengthen your profile"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <WarningIcon color="warning" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Certifications"
                    secondary="Industry certifications could enhance your credibility"
                  />
                </ListItem>
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
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2">Cloud Computing (AWS/Azure)</Typography>
                  <Typography variant="body2" color="text.secondary">60%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={60} sx={{ height: 8, borderRadius: 4 }} />
              </Box>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2">DevOps & CI/CD</Typography>
                  <Typography variant="body2" color="text.secondary">45%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={45} color="warning" sx={{ height: 8, borderRadius: 4 }} />
              </Box>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2">Machine Learning</Typography>
                  <Typography variant="body2" color="text.secondary">30%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={30} color="error" sx={{ height: 8, borderRadius: 4 }} />
              </Box>
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
                {['Senior Software Engineer', 'Full Stack Developer', 'DevOps Engineer', 'Technical Lead'].map((role) => (
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
                      Match: 85% | High demand
                    </Typography>
                  </Box>
                ))}
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
                  { title: 'Current Level', description: 'Mid-level Software Engineer', time: 'Now' },
                  { title: 'Next 6 Months', description: 'Gain cloud certifications and DevOps experience', time: '6 months' },
                  { title: 'Next 1 Year', description: 'Transition to Senior Engineer or Technical Lead', time: '1 year' },
                  { title: 'Long-term Goal', description: 'Architect or Engineering Manager role', time: '2-3 years' },
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

