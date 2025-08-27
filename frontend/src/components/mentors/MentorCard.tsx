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
} from '@mui/icons-material';
import { Mentor } from '../../types';

interface MentorCardProps {
  mentor: Mentor;
  onFavorite: (mentorId: number) => void;
  isFavorite: boolean;
  onBookAppointment?: (mentorId: number) => void;
}

const MentorCard: React.FC<MentorCardProps> = ({
  mentor,
  onFavorite,
  isFavorite,
  onBookAppointment,
}) => {
  const [detailsOpen, setDetailsOpen] = useState(false);

  const handleBookAppointment = () => {
    if (onBookAppointment) {
      onBookAppointment(mentor.id);
    }
  };

  return (
    <>
      <Card
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          transition: 'transform 0.2s, box-shadow 0.2s',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: 4,
          },
        }}
      >
        <CardContent sx={{ flexGrow: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
            <Avatar
              src={mentor.avatar}
              sx={{ width: 60, height: 60, mr: 2 }}
            >
              {mentor.first_name?.[0]}{mentor.last_name?.[0]}
            </Avatar>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h6" component="div" gutterBottom>
                {mentor.first_name} {mentor.last_name}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {mentor.title} at {mentor.company}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Rating value={mentor.rating || 0} readOnly size="small" />
                <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                  ({mentor.review_count || 0} reviews)
                </Typography>
              </Box>
            </Box>
            <IconButton
              onClick={() => onFavorite(mentor.id)}
              color="primary"
              size="small"
            >
              {isFavorite ? <Favorite /> : <FavoriteBorder />}
            </IconButton>
          </Box>

          <Typography variant="body2" color="text.secondary" gutterBottom>
            {mentor.bio?.substring(0, 100)}...
          </Typography>

          <Box sx={{ mt: 2, mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Expertise:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {mentor.skills?.slice(0, 3).map((skill, index) => (
                <Chip
                  key={index}
                  label={skill}
                  size="small"
                  variant="outlined"
                  color="primary"
                />
              ))}
              {mentor.skills && mentor.skills.length > 3 && (
                <Chip
                  label={`+${mentor.skills.length - 3} more`}
                  size="small"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <LocationOn fontSize="small" color="action" sx={{ mr: 1 }} />
            <Typography variant="body2" color="text.secondary">
              {mentor.location || 'Remote'}
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Work fontSize="small" color="action" sx={{ mr: 1 }} />
            <Typography variant="body2" color="text.secondary">
              {mentor.experience_years || 0} years experience
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 2 }}>
            <Typography variant="h6" color="primary">
              ${mentor.hourly_rate || 0}/hr
            </Typography>
            <Chip
              label={mentor.availability_status || 'Available'}
              color={mentor.availability_status === 'Available' ? 'success' : 'default'}
              size="small"
            />
          </Box>
        </CardContent>

        <CardActions sx={{ justifyContent: 'space-between', p: 2 }}>
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
        </CardActions>
      </Card>

      {/* Mentor Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Avatar
              src={mentor.avatar}
              sx={{ width: 60, height: 60, mr: 2 }}
            >
              {mentor.first_name?.[0]}{mentor.last_name?.[0]}
            </Avatar>
            <Box>
              <Typography variant="h5">
                {mentor.first_name} {mentor.last_name}
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
                {mentor.experience_years} years of experience in {mentor.industry}
              </Typography>

              <Typography variant="h6" gutterBottom>
                Education
              </Typography>
              <Typography variant="body1" paragraph>
                {mentor.education}
              </Typography>

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
                    ${mentor.hourly_rate}/hr
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Rating
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Rating value={mentor.rating || 0} readOnly />
                    <Typography variant="body2" sx={{ ml: 1 }}>
                      ({mentor.review_count || 0} reviews)
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
    </>
  );
};

export default MentorCard;