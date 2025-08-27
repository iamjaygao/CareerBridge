import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  TextField,
  InputAdornment,
  Snackbar,
  Alert,
  Typography,
} from '@mui/material';
import { Grid, Pagination } from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { AppDispatch, RootState } from '../../store';
import { fetchMentors, setFilters, clearFilters } from '../../store/slices/mentorSlice';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import MentorFilterBar from '../../components/mentors/MentorFilterBar';
import MentorCard from '../../components/mentors/MentorCard';
import BookingDialog from '../../components/appointments/BookingDialog';
import { MentorFilters } from '../../services/api/mentorService';
import { Mentor } from '../../types';

const MentorListPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { mentors, loading, error, filters } = useSelector((state: RootState) => state.mentors);
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
    dispatch(fetchMentors({ ...filters, page }));
  }, [dispatch, filters, page]);

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
    const mentor = mentors.find(m => m.id === mentorId);
    if (mentor) {
      setSelectedMentor(mentor);
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

  if (loading) {
    return <LoadingSpinner message="Loading mentors..." />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  return (
    <>
      <PageHeader
        title="Find Mentors"
        breadcrumbs={[{ label: 'Mentors', path: '/mentors' }]}
      />

      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search mentors by name, skills, or industry..."
          value={searchTerm}
          onChange={handleSearch}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ mb: 3 }}
        />

        <MentorFilterBar
          filters={filters}
          onFilterChange={handleFilterChange}
          onFilterClear={handleFilterClear}
        />
      </Box>

      <Grid container spacing={3}>
        {mentors.length > 0 ? (
          mentors.map((mentor) => (
            <Grid item xs={12} sm={6} md={4} key={mentor.id}>
              <MentorCard
                mentor={mentor}
                onFavorite={handleFavorite}
                isFavorite={favorites.includes(mentor.id)}
                onBookAppointment={handleBookAppointment}
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
                borderRadius: 1,
              }}
            >
              <Typography variant="h6" gutterBottom>
                No mentors found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Try adjusting your filters or search terms
              </Typography>
            </Box>
          </Grid>
        )}
      </Grid>

      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
        <Pagination page={page} onChange={(_, p) => setPage(p)} count={10} color="primary" />
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
    </>
  );
};

export default MentorListPage; 