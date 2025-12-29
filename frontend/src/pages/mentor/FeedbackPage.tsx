import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Rating,
  Avatar,
  Chip,
  Divider,
  Alert,
} from '@mui/material';
import {
  Star as StarIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import mentorService from '../../services/api/mentorService';

interface Feedback {
  id: number;
  student: {
    name: string;
    avatar?: string;
  };
  rating: number;
  comment: string;
  session_type: string;
  date: string;
}

const MentorFeedbackPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState({
    averageRating: 0,
    totalReviews: 0,
  });
  const [ratingCounts, setRatingCounts] = useState<Record<number, number>>({});
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);

  useEffect(() => {
    const fetchFeedback = async () => {
      try {
        setError(null);
        const profile = await mentorService.getMyProfile();
        const mentorId = profile?.id;
        if (!mentorId) {
          setError('Mentor profile not found.');
          return;
        }

        const reviews = await mentorService.getMentorReviews(mentorId);
        const list = Array.isArray(reviews) ? reviews : ((reviews as any)?.results || []);
        const mapped = list.map((review: any) => {
          const studentName = review.user
            ? `${review.user.first_name || ''} ${review.user.last_name || ''}`.trim() || review.user.username
            : 'Student';
          return {
            id: review.id,
            student: {
              name: studentName,
              avatar: review.user?.avatar,
            },
            rating: review.rating,
            comment: review.comment,
            session_type: 'Session',
            date: review.created_at,
          } as Feedback;
        });

        const totalReviews = mapped.length;
        const averageRating = totalReviews
          ? mapped.reduce((sum: number, item: Feedback) => sum + (item.rating || 0), 0) / totalReviews
          : 0;
        const counts = mapped.reduce((acc: Record<number, number>, item: Feedback) => {
          const rating = Math.round(item.rating || 0);
          if (!rating) return acc;
          acc[rating] = (acc[rating] || 0) + 1;
          return acc;
        }, {} as Record<number, number>);

        setSummary({
          averageRating: Number(averageRating.toFixed(1)),
          totalReviews,
        });
        setRatingCounts(counts);
        setFeedbacks(mapped);
      } catch {
        setError('Failed to load feedback.');
      } finally {
        setLoading(false);
      }
    };

    fetchFeedback();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading feedback..." />;
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Feedback & Reviews
        </Typography>
        <Typography variant="body2" color="text.secondary">
          View feedback from your students
        </Typography>
      </Box>

      {/* Summary Card */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    bgcolor: 'primary.light',
                    color: 'primary.main',
                  }}
                >
                  <StarIcon sx={{ fontSize: 40 }} />
                </Box>
                <Box>
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {summary.averageRating}
                  </Typography>
                  <Rating value={summary.averageRating} precision={0.1} readOnly size="large" />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Based on {summary.totalReviews} reviews
                  </Typography>
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {[5, 4, 3, 2, 1].map((rating) => {
                  const count = ratingCounts[rating] || 0;
                  return (
                    <Box key={rating} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" sx={{ minWidth: 40 }}>
                        {rating} star
                      </Typography>
                      <Box sx={{ flexGrow: 1, height: 8, bgcolor: 'grey.200', borderRadius: 1, position: 'relative' }}>
                        <Box
                          sx={{
                            height: '100%',
                            width: summary.totalReviews ? `${(count / summary.totalReviews) * 100}%` : '0%',
                            bgcolor: 'primary.main',
                            borderRadius: 1,
                          }}
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ minWidth: 40 }}>
                        {count}
                      </Typography>
                    </Box>
                  );
                })}
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Feedback List */}
      <Box>
        <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
          Recent Reviews
        </Typography>
        <Grid container spacing={3}>
          {feedbacks.map((feedback) => (
            <Grid item xs={12} key={feedback.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'start', mb: 2 }}>
                    <Avatar sx={{ mr: 2, width: 48, height: 48 }}>
                      {feedback.student.name.charAt(0)}
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {feedback.student.name}
                        </Typography>
                        <Rating value={feedback.rating} readOnly size="small" />
                      </Box>
                      <Chip label={feedback.session_type} size="small" sx={{ mr: 1 }} />
                      <Typography variant="caption" color="text.secondary">
                        {new Date(feedback.date).toLocaleDateString()}
                      </Typography>
                    </Box>
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    {feedback.comment}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Box>
  );
};

export default MentorFeedbackPage;
