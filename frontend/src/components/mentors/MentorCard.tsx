import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Chip,
  Button,
  Avatar,
  Rating,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Divider,
  IconButton,
} from '@mui/material';
import {
  Favorite,
  FavoriteBorder,
  Schedule,
  LocationOn,
  Work,
  School,
  Star,
  Message,
  Lock,
  LockOpen,
} from '@mui/icons-material';
import { Mentor } from '../../types';

interface MentorCardProps {
  mentor: Mentor;
  onFavorite?: (mentorId: number) => void;
  isFavorite?: boolean;
  onBookAppointment?: (mentorId: number) => void;
  isVisitor?: boolean; // If true, show limited information for visitors
}

const MentorCard: React.FC<MentorCardProps> = ({
  mentor,
  onFavorite,
  isFavorite,
  onBookAppointment,
  isVisitor = false,
}) => {
  const [detailsOpen, setDetailsOpen] = useState(false);

  const handleBookAppointment = () => {
    if (onBookAppointment) {
      onBookAppointment(mentor.id);
    }
  };

  // Generate placeholder data for visitors
  const getPreviousCompany = () => {
    if (mentor.company) {
      return `Ex-${mentor.company}`;
    }
    const companies = ['Amazon', 'Google', 'Meta', 'Microsoft', 'Apple', 'Netflix'];
    return `Ex-${companies[mentor.id % companies.length]}`;
  };

  const getExperienceYears = () => {
    const years = mentor.experience_years || mentor.years_of_experience || 0;
    return years > 0 ? `${years}+ yrs experience` : '8+ yrs experience';
  };

  const getHighlights = () => {
    const studentsHelped = 20 + (mentor.id % 30); // 20-50 range
    const specializations = mentor.skills || mentor.expertise || ['Backend', 'System Design', 'Resume Review'];
    const primarySpec = specializations[0] || 'SWE';
    
    return [
      `Helped ${studentsHelped}+ students land internships`,
      `${primarySpec} / ${specializations[1] || 'Backend'} / ${specializations[2] || 'System Design'} Specialist`,
      'FAANG mock interview experience',
    ];
  };

  const getExpertiseTags = () => {
    const skills = mentor.skills || mentor.expertise || [];
    if (skills.length > 0) {
      return skills.slice(0, 4);
    }
    return ['Backend', 'System Design', 'Resume Review', 'Interview Prep'];
  };

  const getSpecializationTag = () => {
    const skills = mentor.skills || mentor.expertise || [];
    if (skills.length > 0) {
      const primary = skills[0];
      const secondary = skills[1] || 'Interview Prep';
      return `${primary} & ${secondary}`;
    }
    return 'Product Strategy & Interview Prep';
  };

  return (
    <>
      <Card
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          transition: 'transform 0.2s, box-shadow 0.2s',
          borderRadius: isVisitor ? '20px' : '16px',
          boxShadow: isVisitor ? 4 : 2,
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: isVisitor ? 8 : 4,
          },
        }}
      >
        <CardContent sx={{ flexGrow: 1, p: isVisitor ? 5 : 3 }}>
          {/* Header Area */}
          <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: isVisitor ? 3 : 2.5 }}>
            <Avatar
              src={isVisitor ? undefined : (mentor.avatar || (typeof mentor.user === 'object' ? mentor.user.avatar : undefined))}
              sx={{ 
                width: isVisitor ? 72 : 64, 
                height: isVisitor ? 72 : 64, 
                mr: 2,
                fontSize: isVisitor ? '1.75rem' : '1.5rem',
                fontWeight: 600,
                ...(isVisitor && {
                  filter: 'blur(4px)',
                  bgcolor: 'grey.300',
                })
              }}
            >
              {typeof mentor.user === 'object' 
                ? `${mentor.user.first_name?.[0] || ''}${mentor.user.last_name?.[0] || ''}`.trim() || mentor.user.username?.[0] || 'M'
                : 'M'}
            </Avatar>
            <Box sx={{ flexGrow: 1 }}>
              <Typography 
                variant={isVisitor ? 'h5' : 'h6'}
                component="div" 
                gutterBottom
                sx={{ 
                  fontWeight: 600,
                  fontSize: isVisitor ? '1.5rem' : '1.25rem',
                  mb: 0.5,
                  lineHeight: 1.2,
                }}
              >
                {isVisitor 
                  ? (typeof mentor.user === 'object' 
                      ? `${mentor.user.first_name?.[0] || ''}${mentor.user.last_name?.[0] || ''}`.trim() || mentor.user.username?.[0] || 'M'
                      : 'M')
                  : (typeof mentor.user === 'object' 
                      ? `${mentor.user.first_name || ''} ${mentor.user.last_name || ''}`.trim() || mentor.user.username
                      : 'Mentor')}
              </Typography>
              {isVisitor ? (
                <>
                  <Typography 
                    variant="body2" 
                    color="text.secondary" 
                    sx={{ 
                      mb: 0.75, 
                      fontWeight: 500,
                      fontSize: '0.875rem',
                    }}
                  >
                    {getPreviousCompany()} • {getExperienceYears()}
                  </Typography>
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      color: 'text.secondary',
                      fontSize: '0.813rem',
                      fontStyle: 'italic',
                    }}
                  >
                    🏆 Specializes in {getSpecializationTag()}
                  </Typography>
                </>
              ) : (
                <>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {mentor.company || mentor.current_position || 'Professional'}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Rating value={mentor.rating || 0} readOnly size="small" />
                    <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                      ({(mentor.review_count || mentor.reviews_count || 0)} reviews)
                    </Typography>
                  </Box>
                </>
              )}
            </Box>
            {onFavorite && !isVisitor && (
              <IconButton
                onClick={() => onFavorite(mentor.id)}
                color="primary"
                size="small"
              >
                {isFavorite ? <Favorite /> : <FavoriteBorder />}
              </IconButton>
            )}
          </Box>

          {/* For visitors: show highlights section; for students: show bio */}
          {isVisitor ? (
            <>
              {/* Highlights Section */}
              <Box sx={{ mb: 3 }}>
                <Typography 
                  variant="subtitle2" 
                  sx={{ 
                    fontWeight: 600, 
                    mb: 1.5, 
                    fontSize: '0.875rem',
                    color: 'text.primary',
                  }}
                >
                  Highlights:
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.25 }}>
                  {getHighlights().map((highlight, index) => (
                    <Box
                      key={index}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        position: 'relative',
                        px: 1.5,
                        py: 1.25,
                        borderRadius: '8px',
                        bgcolor: 'grey.100',
                      }}
                    >
                      <Typography
                        variant="body2"
                        sx={{
                          flex: 1,
                          filter: 'blur(2px)',
                          color: 'text.secondary',
                          fontSize: '0.813rem',
                          opacity: 0.7,
                        }}
                      >
                        {highlight}
                      </Typography>
                      <Lock sx={{ fontSize: '1rem', color: 'text.secondary', ml: 1.5, flexShrink: 0, opacity: 0.6 }} />
                    </Box>
                  ))}
                </Box>
              </Box>

              {/* Expertise Tags - Blurred */}
              <Box sx={{ mb: 2.5 }}>
                <Typography 
                  variant="subtitle2" 
                  sx={{ 
                    fontWeight: 600, 
                    mb: 1.25, 
                    fontSize: '0.875rem',
                    color: 'text.primary',
                  }}
                >
                  Expertise:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, position: 'relative' }}>
                  {getExpertiseTags().map((tag: string, index: number) => (
                    <Chip
                      key={index}
                      label={tag}
                      size="small"
                      sx={{
                        filter: 'blur(2px)',
                        borderRadius: '16px',
                        fontSize: '0.75rem',
                        height: '28px',
                        bgcolor: 'grey.100',
                        color: 'text.secondary',
                        border: 'none',
                        opacity: 0.7,
                      }}
                    />
                  ))}
                </Box>
              </Box>
            </>
          ) : (
            <>
              {/* For authenticated users: show bio */}
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {mentor.bio?.substring(0, 100) + (mentor.bio && mentor.bio.length > 100 ? '...' : '')}
              </Typography>

              {/* Skills/Expertise */}
              <Box sx={{ mt: 2, mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Expertise:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {(mentor.skills || mentor.expertise || []).slice(0, 3).map((skill: string, index: number) => (
                    <Chip
                      key={index}
                      label={skill}
                      size="small"
                      variant="outlined"
                      color="primary"
                    />
                  ))}
                  {(mentor.skills || mentor.expertise || []).length > 3 && (
                    <Chip
                      label={`+${(mentor.skills || mentor.expertise || []).length - 3} more`}
                      size="small"
                      variant="outlined"
                    />
                  )}
                </Box>
              </Box>

              {/* Location and Experience */}
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <LocationOn fontSize="small" color="action" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  {mentor.location || 'Remote'}
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Work fontSize="small" color="action" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  {(mentor.experience_years || mentor.years_of_experience || 0)} years experience
                </Typography>
              </Box>

              {/* Pricing */}
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 2 }}>
                <Typography variant="h6" color="primary">
                  ${mentor.hourly_rate || mentor.price_per_hour || 0}/hr
                </Typography>
                <Chip
                  label={mentor.availability_status || 'Available'}
                  color={mentor.availability_status === 'Available' ? 'success' : 'default'}
                  size="small"
                />
              </Box>
            </>
          )}
        </CardContent>

        <CardActions sx={{ p: isVisitor ? 3 : 2, pt: isVisitor ? 2 : 0 }}>
          {isVisitor ? (
            <Box sx={{ width: '100%' }}>
              <Button
                variant="contained"
                fullWidth
                onClick={() => window.location.href = '/register'}
                startIcon={<LockOpen sx={{ fontSize: '1.125rem' }} />}
                sx={{
                  bgcolor: '#1976d2',
                  color: 'white',
                  fontWeight: 500,
                  py: 1.75,
                  borderRadius: '12px',
                  boxShadow: '0 2px 8px rgba(25, 118, 210, 0.3)',
                  '&:hover': {
                    bgcolor: '#1565c0',
                    boxShadow: '0 4px 12px rgba(25, 118, 210, 0.4)',
                  },
                  textTransform: 'none',
                  fontSize: '0.938rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 1,
                }}
              >
                Unlock Full Mentor Profile
              </Button>
              <Typography
                variant="caption"
                sx={{
                  display: 'block',
                  textAlign: 'center',
                  mt: 1.25,
                  color: 'text.secondary',
                  fontSize: '0.75rem',
                  lineHeight: 1.5,
                }}
              >
                Free — view availability, pricing, and success stories
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  display: 'block',
                  textAlign: 'center',
                  mt: 0.5,
                  color: 'text.secondary',
                  fontSize: '0.688rem',
                  opacity: 0.8,
                }}
              >
                No spam. Cancel anytime.
              </Typography>
            </Box>
          ) : (
            <>
              <Button
                size="small"
                onClick={() => setDetailsOpen(true)}
                startIcon={<Message />}
              >
                View Details
              </Button>
              <Button
                variant="contained"
                size="small"
                onClick={handleBookAppointment}
                startIcon={<Schedule />}
                disabled={mentor.availability_status !== 'Available'}
              >
                Book Session
              </Button>
            </>
          )}
        </CardActions>
      </Card>

      {/* Mentor Details Dialog - Only for authenticated users */}
      {!isVisitor && (
        <Dialog
          open={detailsOpen}
          onClose={() => setDetailsOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Avatar
              src={mentor.avatar || (typeof mentor.user === 'object' ? mentor.user.avatar : undefined)}
              sx={{ width: 60, height: 60, mr: 2 }}
            >
              {typeof mentor.user === 'object' 
                ? `${mentor.user.first_name?.[0] || ''}${mentor.user.last_name?.[0] || ''}`.trim() || mentor.user.username?.[0] || 'M'
                : 'M'}
            </Avatar>
            <Box>
              <Typography variant="h5">
                {typeof mentor.user === 'object' 
                  ? `${mentor.user.first_name || ''} ${mentor.user.last_name || ''}`.trim() || mentor.user.username
                  : 'Mentor'}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {mentor.title} at {mentor.company}
              </Typography>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Typography variant="h6" gutterBottom>
                About
              </Typography>
              <Typography variant="body1" paragraph>
                {mentor.bio}
              </Typography>

              <Typography variant="h6" gutterBottom>
                Experience
              </Typography>
              <Typography variant="body1" paragraph>
                {(mentor.experience_years || mentor.years_of_experience || 0)} years of experience{mentor.industry ? ` in ${mentor.industry}` : ''}
              </Typography>

              {mentor.education && (
                <>
                  <Typography variant="h6" gutterBottom>
                    Education
                  </Typography>
                  <Typography variant="body1" paragraph>
                    {mentor.education}
                  </Typography>
                </>
              )}

              <Typography variant="h6" gutterBottom>
                Skills & Expertise
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                {mentor.skills?.map((skill, index) => (
                  <Chip
                    key={index}
                    label={skill}
                    color="primary"
                    variant="outlined"
                  />
                ))}
              </Box>
            </Grid>

            <Grid item xs={12} md={4}>
              <Box sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>
                <Typography variant="h6" gutterBottom>
                  Session Details
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Hourly Rate
                  </Typography>
                  <Typography variant="h5" color="primary">
                    ${mentor.hourly_rate || mentor.price_per_hour || 0}/hr
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Rating
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Rating value={mentor.rating || 0} readOnly />
                    <Typography variant="body2" sx={{ ml: 1 }}>
                      ({(mentor.review_count || mentor.reviews_count || 0)} reviews)
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Location
                  </Typography>
                  <Typography variant="body2">
                    {mentor.location || 'Remote'}
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Availability
                  </Typography>
                  <Chip
                    label={mentor.availability_status || 'Available'}
                    color={mentor.availability_status === 'Available' ? 'success' : 'default'}
                  />
                </Box>

                <Button
                  variant="contained"
                  fullWidth
                  onClick={handleBookAppointment}
                  disabled={mentor.availability_status !== 'Available'}
                  startIcon={<Schedule />}
                >
                  Book Session
                </Button>
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
        </DialogActions>
        </Dialog>
      )}
    </>
  );
};

export default MentorCard;