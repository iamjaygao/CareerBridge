import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Paper,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Description as DescriptionIcon,
  QuestionAnswer as QuestionAnswerIcon,
  Map as MapIcon,
  ArrowForward as ArrowForwardIcon,
  Article as ArticleIcon,
  AccessTime as AccessTimeIcon,
} from '@mui/icons-material';

const ResourcesPage: React.FC = () => {
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem('access_token');

  const resourceCategories = [
    {
      title: 'Resume Tips',
      description: 'Learn how to craft a resume that stands out with expert advice and AI-backed recommendations.',
      icon: <DescriptionIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
      buttonText: 'View Tips',
      link: '/resources/resume-tips',
    },
    {
      title: 'Interview Guide',
      description: 'Master job interviews with structured frameworks, example answers, and preparation checklists.',
      icon: <QuestionAnswerIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
      buttonText: 'View Guide',
      link: '/resources/interview-guide',
    },
    {
      title: 'Career Roadmaps',
      description: 'Explore step-by-step skill roadmaps for software engineering, data science, product, and more.',
      icon: <MapIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
      buttonText: 'View Roadmaps',
      link: '/resources/career-roadmaps',
    },
  ];

  const popularArticles = [
    {
      title: 'How to Write a Resume That Gets Past ATS Systems',
      description: 'Learn the key strategies for optimizing your resume to pass Applicant Tracking Systems and reach human recruiters.',
      readTime: '5 min read',
      category: 'Resume Tips',
    },
    {
      title: 'Top 10 Interview Questions and How to Answer Them',
      description: 'Master the most common interview questions with proven frameworks and example answers that impress hiring managers.',
      readTime: '8 min read',
      category: 'Interview Guide',
    },
    {
      title: 'Software Engineering Career Path: From Junior to Senior',
      description: 'A comprehensive roadmap outlining the skills, experience, and milestones needed to advance in software engineering.',
      readTime: '12 min read',
      category: 'Career Roadmaps',
    },
    {
      title: 'Data Science Career Guide: Skills and Opportunities',
      description: 'Discover the essential skills, tools, and career paths available in the rapidly growing field of data science.',
      readTime: '10 min read',
      category: 'Career Roadmaps',
    },
    {
      title: 'How to Negotiate Your Salary: A Complete Guide',
      description: 'Practical strategies and scripts for negotiating your salary with confidence and achieving better compensation.',
      readTime: '7 min read',
      category: 'Interview Guide',
    },
  ];

  return (
    <Box sx={{ width: '100%', maxWidth: '1200px', mx: 'auto', px: { xs: 2, sm: 3, md: 6 }, py: { xs: 4, md: 6 } }}>
      {/* Hero Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: { xs: 6, md: 8 },
          px: { xs: 3, md: 4 },
          borderRadius: { xs: 0, md: 3 },
          mb: 8,
          textAlign: 'center',
        }}
      >
        <Typography
          variant="h2"
          component="h1"
          sx={{
            fontWeight: 700,
            fontSize: { xs: '2rem', md: '3rem' },
            color: 'white',
            mb: 2,
            lineHeight: 1.2,
          }}
        >
          Career Resources & Insights
        </Typography>
        <Typography
          variant="h5"
          component="p"
          sx={{
            fontSize: { xs: '1rem', md: '1.25rem' },
            color: 'rgba(255, 255, 255, 0.95)',
            maxWidth: '700px',
            mx: 'auto',
            lineHeight: 1.6,
          }}
        >
          Guides, tips, and tools to help you navigate your career journey.
        </Typography>
      </Box>

      {/* Resource Categories Section */}
      <Box sx={{ mb: 10 }}>
        <Typography
          variant="h3"
          component="h2"
          align="center"
          sx={{
            fontWeight: 700,
            fontSize: { xs: '2rem', md: '2.5rem' },
            mb: 6,
            color: 'text.primary',
          }}
        >
          Explore Our Resources
        </Typography>
        <Grid container spacing={4}>
          {resourceCategories.map((category, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'all 0.3s',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: 8,
                  },
                  border: '1px solid',
                  borderColor: 'grey.200',
                }}
              >
                <CardContent sx={{ flexGrow: 1, p: 4, textAlign: 'center' }}>
                  <Box sx={{ mb: 3 }}>{category.icon}</Box>
                  <Typography
                    variant="h5"
                    component="h3"
                    sx={{
                      fontWeight: 700,
                      mb: 2,
                      color: 'text.primary',
                    }}
                  >
                    {category.title}
                  </Typography>
                  <Typography
                    variant="body1"
                    sx={{
                      color: 'text.secondary',
                      lineHeight: 1.6,
                      mb: 3,
                    }}
                  >
                    {category.description}
                  </Typography>
                </CardContent>
                <CardActions sx={{ p: 4, pt: 0, justifyContent: 'center' }}>
                  <Button
                    variant="outlined"
                    endIcon={<ArrowForwardIcon />}
                    onClick={() => navigate(category.link)}
                    sx={{
                      textTransform: 'none',
                      fontWeight: 600,
                      px: 3,
                      py: 1,
                    }}
                  >
                    {category.buttonText}
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Popular Articles Section */}
      <Box sx={{ mb: 10 }}>
        <Typography
          variant="h3"
          component="h2"
          sx={{
            fontWeight: 700,
            fontSize: { xs: '2rem', md: '2.5rem' },
            mb: 4,
            color: 'text.primary',
          }}
        >
          Popular Articles
        </Typography>
        <Paper
          elevation={0}
          sx={{
            border: '1px solid',
            borderColor: 'grey.200',
            borderRadius: 2,
            overflow: 'hidden',
          }}
        >
          <List>
            {popularArticles.map((article, index) => (
              <React.Fragment key={index}>
                <ListItem
                  sx={{
                    py: 3,
                    px: 4,
                    '&:hover': {
                      bgcolor: 'grey.50',
                      cursor: 'pointer',
                    },
                  }}
                  onClick={() => {
                    // Placeholder: could navigate to article page
                    console.log(`Navigate to article: ${article.title}`);
                  }}
                >
                  <ArticleIcon
                    sx={{
                      color: 'primary.main',
                      fontSize: 32,
                      mr: 3,
                      flexShrink: 0,
                    }}
                  />
                  <ListItemText
                    primary={
                      <Typography
                        variant="h6"
                        sx={{
                          fontWeight: 600,
                          mb: 1,
                          color: 'text.primary',
                        }}
                      >
                        {article.title}
                      </Typography>
                    }
                    secondary={
                      <Box>
                        <Typography
                          variant="body2"
                          sx={{
                            color: 'text.secondary',
                            mb: 1,
                            lineHeight: 1.6,
                          }}
                        >
                          {article.description}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
                          <Typography
                            variant="caption"
                            sx={{
                              color: 'text.secondary',
                              fontWeight: 500,
                            }}
                          >
                            {article.category}
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <AccessTimeIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                            <Typography
                              variant="caption"
                              sx={{
                                color: 'text.secondary',
                              }}
                            >
                              {article.readTime}
                            </Typography>
                          </Box>
                        </Box>
                      </Box>
                    }
                  />
                  <ArrowForwardIcon
                    sx={{
                      color: 'text.secondary',
                      ml: 2,
                      flexShrink: 0,
                    }}
                  />
                </ListItem>
                {index < popularArticles.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </Paper>
      </Box>

      {/* CTA Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: { xs: 6, md: 8 },
          px: { xs: 3, md: 6 },
          borderRadius: { xs: 0, md: 3 },
          textAlign: 'center',
        }}
      >
        <Typography
          variant="h3"
          component="h2"
          sx={{
            fontWeight: 700,
            fontSize: { xs: '2rem', md: '2.5rem' },
            color: 'white',
            mb: 2,
          }}
        >
          Get personalized insights to accelerate your career.
        </Typography>
        <Typography
          variant="h6"
          sx={{
            color: 'rgba(255, 255, 255, 0.9)',
            mb: 4,
            maxWidth: '600px',
            mx: 'auto',
          }}
        >
          Start your free assessment and get AI-powered recommendations tailored to your career goals.
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={() => navigate(isAuthenticated ? '/dashboard/assessment' : '/register')}
          endIcon={<ArrowForwardIcon />}
          sx={{
            bgcolor: 'white',
            color: 'primary.main',
            px: 5,
            py: 1.5,
            fontSize: '1.1rem',
            fontWeight: 600,
            textTransform: 'none',
            borderRadius: '8px',
            '&:hover': {
              bgcolor: 'rgba(255, 255, 255, 0.9)',
              transform: 'translateY(-2px)',
              boxShadow: '0 8px 16px rgba(0,0,0,0.2)',
            },
            transition: 'all 0.3s',
          }}
        >
          Start Free Assessment
        </Button>
      </Box>
    </Box>
  );
};

export default ResourcesPage;

