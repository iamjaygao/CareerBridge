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
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Work as WorkIcon,
  Star as StarIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const StudentIntelligencePage: React.FC = () => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setLoading(false);
    }, 500);
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading market intelligence..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Market Intelligence
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Real-time job market insights and opportunities
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
                    +15%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Software Engineer roles
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                    Last 30 days
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
                    $120K
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Average salary
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                    Software Engineer (US)
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
          {[
            { title: 'Senior Software Engineer', company: 'Tech Corp', location: 'San Francisco, CA', match: 92 },
            { title: 'Full Stack Developer', company: 'StartupXYZ', location: 'Remote', match: 88 },
            { title: 'DevOps Engineer', company: 'CloudTech', location: 'Austin, TX', match: 85 },
          ].map((job, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {job.title}
                    </Typography>
                    <Chip label={`${job.match}% match`} color="success" size="small" />
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {job.company}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {job.location}
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
            {[
              'React', 'Node.js', 'Python', 'AWS', 'Docker', 'Kubernetes',
              'TypeScript', 'GraphQL', 'MongoDB', 'PostgreSQL', 'CI/CD', 'Microservices'
            ].map((skill) => (
              <Chip
                key={skill}
                label={skill}
                color="primary"
                variant="outlined"
                sx={{ fontWeight: 500 }}
              />
            ))}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default StudentIntelligencePage;

