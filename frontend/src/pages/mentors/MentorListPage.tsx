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
} from '@mui/material';
import { ArrowForward as ArrowForwardIcon } from '@mui/icons-material';

import { AppDispatch, RootState } from '../../store';
import {
  fetchMentors,
  setFilters,
  clearFilters,
} from '../../store/slices/mentorSlice';

import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import MentorFilterBar from '../../components/mentors/MentorFilterBar';
import MentorCard from '../../components/mentors/MentorCard';

import { MentorFilters } from '../../services/api/mentorService';
import { getUserRole, canViewFullMentorList } from '../../utils/permissions';

const MentorListPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();

  const { mentors: mentorList, loading, error, filters,count } = useSelector(
    (state: RootState) => state.mentors
  );
  const { isAuthenticated, user } = useSelector(
    (state: RootState) => state.auth
  );

  const userRole = getUserRole(isAuthenticated, user?.role);
  const canViewFull = canViewFullMentorList(userRole);

  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);

  const PRIMARY_TRACK_LABELS: Record<string, string> = {
    resume_review: 'resume review',
    mock_interview: 'interview preparation',
    career_switch: 'career switching',
    advanced_interview: 'system design interviews',
  };

  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const PAGE_SIZE = 6;
  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE));

  /* =========================
     Data fetching
  ========================= */
  useEffect(() => {
    if (canViewFull) {
      dispatch(fetchMentors({ ...filters, page, limit: 6 }));
    } else {
      if (filters.primary_track) {
        dispatch(fetchMentors({ ...filters, track: filters.primary_track, limit: 6 }));
      } else {
        dispatch(fetchMentors({ ...filters, page: 1, limit: 6 }));
      }
    }
  }, [dispatch, filters, page, canViewFull]);

  /* =========================
     Handlers
  ========================= */
  const handleFilterChange = (patch: Partial<MentorFilters>) => {
    dispatch(setFilters(patch));
  };

  const handleFilterClear = () => {
    setSearchTerm('');
    dispatch(clearFilters());
  };

  if (loading) return <LoadingSpinner message="Loading mentors..." />;
  if (error) return <ErrorAlert message={error} />;


  return (
    <Box
      sx={{
        width: '100%',
        maxWidth: '1200px',
        mx: 'auto',
        px: { xs: 2, sm: 3, md: 6 },
        py: { xs: 4, md: 6 },
      }}
    >
      {/* =========================
          Filters
      ========================= */}
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

      {/* =========================
          Dynamic Heading (when primary_track is set)
      ========================= */}
      {filters.primary_track && PRIMARY_TRACK_LABELS[filters.primary_track] && (
        <Typography variant="h4" sx={{ mt: 2, mb: 4, fontWeight: 700 }}>
          Recommended mentors for {PRIMARY_TRACK_LABELS[filters.primary_track]}
        </Typography>
      )}

      {/* =========================
          Mentor Grid
      ========================= */}
      <Grid container spacing={4}>
        {mentorList.length > 0 ? (
          (() => {
            // When primary_track is set: sort and limit to exactly 6 cards
            const mentorsToRender = filters.primary_track
              ? [...mentorList]
                  .sort((a, b) => {
                    // Priority 1: mentors with badges including "top_pick"
                    const aHasTopPick = a.badges?.includes('top_pick') ?? false;
                    const bHasTopPick = b.badges?.includes('top_pick') ?? false;
                    if (aHasTopPick && !bHasTopPick) return -1;
                    if (!aHasTopPick && bHasTopPick) return 1;

                    // Priority 2: mentors with is_verified === true
                    if (a.is_verified && !b.is_verified) return -1;
                    if (!a.is_verified && b.is_verified) return 1;

                    // Priority 3: higher review_count
                    return (b.review_count ?? 0) - (a.review_count ?? 0);
                  })
                  .slice(0, 6)
              : mentorList;

            return mentorsToRender
              .filter((mentor) => {
                // Filter out mentors with no sellable services (starting_price > 0)
                // Note: List endpoint does NOT include services array, use starting_price instead
                return Number(mentor.starting_price || 0) > 0;
              })
              .map((mentor) => (
                <Grid
                  item
                  xs={12}
                  sm={6}
                  lg={4}
                  key={mentor.id}
                  sx={{ display: 'flex' }}
                >
                  <MentorCard
                    mentor={mentor}
                    isVisitor={!canViewFull}
                    activeTrack={filters.primary_track}
                  />
                </Grid>
              ));
          })()
        ) : (
          <Grid item xs={12}>
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Typography variant="h6">No mentors found</Typography>
              <Typography variant="body2" color="text.secondary">
                Try adjusting your filters.
              </Typography>
            </Box>
          </Grid>
        )}
      </Grid>

      {/* =========================
          Visitor Unlock CTA (hidden when primary_track is set)
      ========================= */}
      {!canViewFull && mentorList.length > 0 && !filters.primary_track && (
        <Paper
          elevation={0}
          sx={{
            mt: 6,
            p: 4,
            textAlign: 'center',
            border: '1px dashed rgba(0,0,0,0.15)',
            borderRadius: 3,
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Unlock full mentor list
          </Typography>

          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mt: 1, mb: 3 }}
          >
            Get matched with mentors based on your goals and experience.
          </Typography>

          <Button
            variant="contained"
            endIcon={<ArrowForwardIcon />}
            onClick={() => navigate('/register')}
            sx={{ textTransform: 'none', fontWeight: 700 }}
          >
            Get started
          </Button>
        </Paper>
      )}

      {/* =========================
          Pagination (members only, hidden when primary_track is set)
      ========================= */}
      {canViewFull && mentorList.length > 0 && !filters.primary_track && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 5 }}>
          <Pagination
            page={page}
            count={totalPages}
            onChange={(_, p) => {
              if (p <= totalPages) {
                setPage(p);
              }
            }}
            color="primary"
          />
        </Box>
      )}

      {/* =========================
          Snackbar
      ========================= */}
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
    </Box>
  );
};

export default MentorListPage;
