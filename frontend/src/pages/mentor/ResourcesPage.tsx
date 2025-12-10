import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
} from '@mui/material';
import {
  MenuBook as HandbookIcon,
  VideoCall as InterviewIcon,
  Gavel as GuidelinesIcon,
  Description as DocsIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';

interface Resource {
  id: number;
  title: string;
  description: string;
  icon: React.ReactNode;
}

const MentorResourcesPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [resources, setResources] = useState<Resource[]>([]);

  useEffect(() => {
    setTimeout(() => {
      setResources([
        {
          id: 1,
          title: 'Mentor Handbook',
          description: 'Complete guide to being an effective mentor on CareerBridge. Learn best practices, platform features, and tips for success.',
          icon: <HandbookIcon sx={{ fontSize: 40 }} />,
        },
        {
          id: 2,
          title: 'How to Run a Great Mock Interview',
          description: 'Step-by-step guide on conducting effective mock interviews that help students prepare for real-world interviews.',
          icon: <InterviewIcon sx={{ fontSize: 40 }} />,
        },
        {
          id: 3,
          title: 'Platform Guidelines & Code of Conduct',
          description: 'Understand the platform rules, professional standards, and code of conduct expected from all mentors.',
          icon: <GuidelinesIcon sx={{ fontSize: 40 }} />,
        },
        {
          id: 4,
          title: 'Resume Review Best Practices',
          description: 'Learn how to provide constructive feedback on resumes that helps students improve their job applications.',
          icon: <DocsIcon sx={{ fontSize: 40 }} />,
        },
      ]);
      setLoading(false);
    }, 500);
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading resources..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Mentor Resources
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Helpful guides and resources to enhance your mentoring
        </Typography>
      </Box>

      {/* Resources Grid */}
      <Grid container spacing={3}>
        {resources.map((resource) => (
          <Grid item xs={12} md={6} key={resource.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: 'primary.light',
                      color: 'primary.main',
                      mr: 2,
                    }}
                  >
                    {resource.icon}
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {resource.title}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {resource.description}
                </Typography>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => {
                    // Placeholder: link to resource
                    alert(`Opening ${resource.title}...`);
                  }}
                >
                  View Resource
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default MentorResourcesPage;

