import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Snackbar,
  Alert,
  Typography,
  Grid,
  Pagination,
  Button,
  Paper,
  Container,
} from '@mui/material';
import { ArrowForward as ArrowForwardIcon } from '@mui/icons-material';
import { AppDispatch, RootState } from '../../store';
import { fetchMentors, setFilters, clearFilters } from '../../store/slices/mentorSlice';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import MentorFilterBar from '../../components/mentors/MentorFilterBar';
import MentorCard from '../../components/mentors/MentorCard';
import BookingDialog from '../../components/appointments/BookingDialog';
import { MentorFilters } from '../../services/api/mentorService';
import { Mentor } from '../../types';
import { getUserRole, canViewFullMentorList, getFeaturedMentorsCount } from '../../utils/permissions';

const MentorListPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { mentors, loading, error, filters } = useSelector((state: RootState) => state.mentors);
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);
  const userRole = getUserRole(isAuthenticated, user?.role);
  const canViewFull = canViewFullMentorList(userRole);
  const featuredCount = getFeaturedMentorsCount(userRole);
  const [searchTerm, setSearchTerm] = useState('');
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });
  const [favorites, setFavorites] = useState<number[]>([]);
  const [page, setPage] = useState(1);
  const [bookingDialogOpen, setBookingDialogOpen] = useState(false);
  const [selectedMentor, setSelectedMentor] = useState<Mentor | null>(null);

  useEffect(() => {
    // For visitors: fetch only featured mentors (limit to 4)
    // For authenticated users: fetch all mentors with pagination
    if (canViewFull) {
      dispatch(fetchMentors({ ...filters, page }));
    } else {
      // Visitors: fetch only featured mentors (no pagination, limit to 4)
      dispatch(fetchMentors({ ...filters, limit: 4 }));
    }
  }, [dispatch, filters, page, canViewFull]);

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setSearchTerm(value);
    dispatch(setFilters({ ...filters, search: value }));
  };

  const handleFilterChange = (newFilters: MentorFilters) => {
    dispatch(setFilters(newFilters));
  };

  const handleFilterClear = () => {
    setSearchTerm('');
    dispatch(clearFilters());
  };

  const handleFavorite = (mentorId: number) => {
    if (favorites.includes(mentorId)) {
      setFavorites(favorites.filter(id => id !== mentorId));
      setSnackbar({
        open: true,
        message: 'Removed from favorites',
        severity: 'success',
      });
    } else {
      setFavorites([...favorites, mentorId]);
      setSnackbar({
        open: true,
        message: 'Added to favorites',
        severity: 'success',
      });
    }
  };

  const handleBookAppointment = (mentorId: number) => {
    if (!isAuthenticated) {
      navigate('/login', { state: { redirectTo: '/mentors' } });
      return;
    }
    const mentor = mentors.find(m => m.id === mentorId);
    if (mentor) {
      setSelectedMentor(mentor as any);
      setBookingDialogOpen(true);
    }
  };

  const handleBookingComplete = () => {
    setSnackbar({
      open: true,
      message: 'Appointment booked successfully!',
      severity: 'success',
    });
  };

  // Show loading and error states for all users
  if (loading) {
    return <LoadingSpinner message="Loading mentors..." />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  return (
    <Box sx={{ width: '100%', maxWidth: '1200px', mx: 'auto', px: { xs: 2, sm: 3, md: 6 }, py: { xs: 4, md: 6 } }}>
      {/* Hero Banner Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: { xs: 6, md: 8 },
          px: { xs: 3, md: 4 },
          borderRadius: { xs: 0, md: 3 },
          mb: 4,
        }}
      >
        <Box>
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', md: 'row' },
              alignItems: { xs: 'flex-start', md: 'center' },
              justifyContent: 'space-between',
              gap: 3,
            }}
          >
            <Box sx={{ flex: 1, maxWidth: { md: '60%' } }}>
              <Typography
                variant="h3"
                component="h1"
                sx={{
                  fontWeight: 700,
                  fontSize: { xs: '2rem', md: '2.75rem' },
                  color: 'white',
                  mb: 2,
                  lineHeight: 1.2,
                }}
              >
                Unlock 1:1 Career Guidance From Top Tech Mentors
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontSize: { xs: '1rem', md: '1.125rem' },
                  color: 'rgba(255, 255, 255, 0.9)',
                  mb: 3,
                  lineHeight: 1.6,
                }}
              >
                Sign up free to access mentor profiles, availability, mock interviews, and personalized guidance for your career growth.
              </Typography>
            </Box>
            <Box
              sx={{
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                gap: 2,
                width: { xs: '100%', md: 'auto' },
                minWidth: { md: '280px' },
              }}
            >
              <Button
                variant="outlined"
                onClick={() => navigate('/login')}
                sx={{
                  textTransform: 'none',
                  fontWeight: 500,
                  py: 1.5,
                  px: 3,
                  borderColor: 'white',
                  color: 'white',
                  '&:hover': {
                    borderColor: 'rgba(255, 255, 255, 0.8)',
                    bgcolor: 'rgba(255, 255, 255, 0.1)',
                  },
                }}
              >
                Sign In
              </Button>
              <Button
                variant="contained"
                onClick={() => navigate('/register')}
                endIcon={<ArrowForwardIcon />}
                sx={{
                  textTransform: 'none',
                  fontWeight: 500,
                  py: 1.5,
                  px: 3,
                  bgcolor: 'white',
                  color: 'primary.main',
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.9)',
                  },
                }}
              >
                Get Started Free
              </Button>
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Filters Section */}
      <Box sx={{ mb: 4 }}>
        <MentorFilterBar
          filters={filters}
          onFilterChange={handleFilterChange}
          onFilterClear={handleFilterClear}
          searchTerm={searchTerm}
          onSearchChange={(value) => {
            setSearchTerm(value);
            dispatch(setFilters({ ...filters, search: value }));
          }}
        />
      </Box>

      {/* Mentor Cards Grid */}
      <Box sx={{ mb: 6 }}>
        <Grid container spacing={4}>
          {mentors.length > 0 ? (
            mentors.map((mentor) => (
              <Grid item xs={12} sm={6} lg={4} key={mentor.id}>
                <MentorCard
                  mentor={mentor as any}
                  onFavorite={canViewFull ? handleFavorite : undefined}
                  isFavorite={canViewFull && favorites.includes(mentor.id)}
                  onBookAppointment={canViewFull ? handleBookAppointment : undefined}
                  isVisitor={!canViewFull}
                />
              </Grid>
            ))
          ) : (
            <Grid item xs={12}>
              <Box
                sx={{
                  textAlign: 'center',
                  py: 8,
                  px: 2,
                  bgcolor: 'background.paper',
                  borderRadius: 2,
                }}
              >
                <Typography variant="h6" gutterBottom>
                  {canViewFull ? 'No mentors found' : 'Featured Mentors'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {canViewFull 
                    ? 'Try adjusting your filters or search terms'
                    : 'Sign up to view all mentors and access full features'}
                </Typography>
              </Box>
            </Grid>
          )}
        </Grid>

        {/* Pagination */}
        {canViewFull && mentors.length > 0 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <Pagination 
              page={page} 
              onChange={(_: React.ChangeEvent<unknown>, p: number) => setPage(p)} 
              count={10} 
              color="primary" 
            />
          </Box>
        )}

        {/* CTA Section for Visitors */}
        {!canViewFull && mentors.length > 0 && (
          <Box sx={{ textAlign: 'center', mt: 6, mb: 4 }}>
            <Paper 
              sx={{ 
                p: 4, 
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                color: 'white',
                borderRadius: 3,
              }}
            >
              <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
                Want to see more mentors?
              </Typography>
              <Typography variant="body1" sx={{ mb: 3, opacity: 0.9, maxWidth: '600px', mx: 'auto' }}>
                Sign up for free to access our full mentor directory, detailed profiles, and book sessions with industry experts.
              </Typography>
              <Button
                variant="contained"
                onClick={() => navigate('/register')}
                endIcon={<ArrowForwardIcon />}
                sx={{
                  bgcolor: 'white',
                  color: 'primary.main',
                  textTransform: 'none',
                  fontWeight: 500,
                  py: 1.5,
                  px: 4,
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.9)',
                  },
                }}
              >
                Sign Up Free
              </Button>
            </Paper>
          </Box>
        )}
      </Box>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      <BookingDialog
        open={bookingDialogOpen}
        onClose={() => setBookingDialogOpen(false)}
        mentor={selectedMentor}
        onBookingComplete={handleBookingComplete}
      />
    </Box>
  );
};

export default MentorListPage; 