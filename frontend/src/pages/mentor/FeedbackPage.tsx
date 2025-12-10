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
} from '@mui/material';
import {
  Star as StarIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';

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
  const [summary, setSummary] = useState({
    averageRating: 4.8,
    totalReviews: 45,
  });
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);

  useEffect(() => {
    setTimeout(() => {
      setFeedbacks([
        {
          id: 1,
          student: { name: 'Alice Johnson' },
          rating: 5,
          comment: 'Excellent mentor! Provided great insights on my career transition. Very helpful and professional.',
          session_type: 'Career Chat',
          date: '2025-01-15T10:00:00Z',
        },
        {
          id: 2,
          student: { name: 'Bob Smith' },
          rating: 5,
          comment: 'The mock interview was incredibly valuable. Helped me identify areas for improvement and build confidence.',
          session_type: 'Mock Interview',
          date: '2025-01-12T14:30:00Z',
        },
        {
          id: 3,
          student: { name: 'Charlie Brown' },
          rating: 4,
          comment: 'Good resume review session. Got helpful feedback on formatting and content structure.',
          session_type: 'Resume Review',
          date: '2025-01-10T09:15:00Z',
        },
        {
          id: 4,
          student: { name: 'Diana Prince' },
          rating: 5,
          comment: 'Amazing mentor! Very knowledgeable and patient. Would definitely book another session.',
          session_type: 'Career Chat',
          date: '2025-01-08T16:00:00Z',
        },
      ]);
      setLoading(false);
    }, 500);
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading feedback..." />;
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
                  const count = Math.floor(summary.totalReviews * (rating === 5 ? 0.6 : rating === 4 ? 0.25 : rating === 3 ? 0.1 : rating === 2 ? 0.04 : 0.01));
                  return (
                    <Box key={rating} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" sx={{ minWidth: 40 }}>
                        {rating} star
                      </Typography>
                      <Box sx={{ flexGrow: 1, height: 8, bgcolor: 'grey.200', borderRadius: 1, position: 'relative' }}>
                        <Box
                          sx={{
                            height: '100%',
                            width: `${(count / summary.totalReviews) * 100}%`,
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

