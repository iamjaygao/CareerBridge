import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Paper,
  TextField,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  Event as EventIcon,
  Article as ArticleIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../../components/common/LoadingSpinner';
import adminService from '../../../services/api/adminService';
import { useNotification } from '../../../components/common/NotificationProvider';

const ReportsPage: React.FC = () => {
  const { showError } = useNotification();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [contentViews, setContentViews] = useState<number | null>(null);
  const [contentItems, setContentItems] = useState<any[]>([]);
  const [rangeStart, setRangeStart] = useState<string>(() => {
    const date = new Date();
    date.setDate(date.getDate() - 30);
    return date.toISOString().split('T')[0];
  });
  const [rangeEnd, setRangeEnd] = useState<string>(() => {
    const date = new Date();
    return date.toISOString().split('T')[0];
  });

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const stats = await adminService.getStaffDashboardStats();
        setDashboardData(stats);
        try {
          const content = await adminService.getContent();
          const list = Array.isArray(content) ? content : (content?.results || []);
          setContentItems(list);
        } catch {
          setContentViews(null);
        }
      } catch {
        showError('Failed to load reports.');
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, [showError]);

  const approvedMentors = dashboardData?.new_mentors_this_month || 0;
  const pendingMentors = dashboardData?.pending_mentor_approvals || 0;
  const totalApplications = approvedMentors + pendingMentors;
  const approvalRate = totalApplications > 0 ? Math.round((approvedMentors / totalApplications) * 100) : null;
  const appointmentMom = dashboardData?.appointment_mom;
  const userMom = dashboardData?.user_mom;

  useEffect(() => {
    if (!contentItems.length) {
      setContentViews(null);
      return;
    }
    const start = new Date(rangeStart);
    const end = new Date(rangeEnd);
    end.setHours(23, 59, 59, 999);
    const totalViews = contentItems.reduce((sum: number, item: any) => {
      if (!item.created_at) return sum;
      const createdAt = new Date(item.created_at);
      if (createdAt >= start && createdAt <= end) {
        return sum + (item.views || 0);
      }
      return sum;
    }, 0);
    setContentViews(totalViews);
  }, [contentItems, rangeStart, rangeEnd]);

  if (loading) {
    return <LoadingSpinner message="Loading reports..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Reports & Insights
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Analytics and performance metrics
        </Typography>
      </Box>

      {/* Report Cards */}
      <Grid container spacing={3}>
        {/* Mentor Approval Rate */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PeopleIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Mentor Approval Rate
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Last 30 days
                  </Typography>
                </Box>
              </Box>
              <Paper
                variant="outlined"
                sx={{
                  p: 3,
                  textAlign: 'center',
                  bgcolor: 'grey.50',
                  minHeight: 200,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Box>
                  <Typography variant="h3" sx={{ fontWeight: 700, color: 'success.main' }}>
                    {approvalRate !== null ? `${approvalRate}%` : 'N/A'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Approval Rate
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {totalApplications > 0
                      ? `${approvedMentors} approved / ${totalApplications} total applications`
                      : 'No applications this month'}
                  </Typography>
                </Box>
              </Paper>
            </CardContent>
          </Card>
        </Grid>

        {/* Appointment Volume */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <EventIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Appointment Volume
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    This month
                  </Typography>
                </Box>
              </Box>
              <Paper
                variant="outlined"
                sx={{
                  p: 3,
                  textAlign: 'center',
                  bgcolor: 'grey.50',
                  minHeight: 200,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Box>
                  <Typography variant="h3" sx={{ fontWeight: 700, color: 'info.main' }}>
                    {dashboardData?.appointments_this_month || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Total Appointments
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {appointmentMom !== undefined && appointmentMom !== null
                      ? `${appointmentMom >= 0 ? '+' : ''}${appointmentMom.toFixed(1)}% vs last month`
                      : 'No comparison data'}
                  </Typography>
                </Box>
              </Paper>
            </CardContent>
          </Card>
        </Grid>

        {/* Content Engagement */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ArticleIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Content Engagement
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, mt: 1, flexWrap: 'wrap' }}>
                    <TextField
                      label="From"
                      type="date"
                      size="small"
                      value={rangeStart}
                      onChange={(e) => setRangeStart(e.target.value)}
                      InputLabelProps={{ shrink: true }}
                    />
                    <TextField
                      label="To"
                      type="date"
                      size="small"
                      value={rangeEnd}
                      onChange={(e) => setRangeEnd(e.target.value)}
                      InputLabelProps={{ shrink: true }}
                    />
                  </Box>
                </Box>
              </Box>
              <Paper
                variant="outlined"
                sx={{
                  p: 3,
                  textAlign: 'center',
                  bgcolor: 'grey.50',
                  minHeight: 200,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Box>
                  <Typography variant="h3" sx={{ fontWeight: 700, color: 'secondary.main' }}>
                    {contentViews !== null ? contentViews.toLocaleString() : 'N/A'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Total Views
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {contentViews !== null ? 'Across all content' : 'Content metrics unavailable'}
                  </Typography>
                </Box>
              </Paper>
            </CardContent>
          </Card>
        </Grid>

        {/* User Growth Trends */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUpIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    User Growth Trends
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Last 30 days
                  </Typography>
                </Box>
              </Box>
              <Paper
                variant="outlined"
                sx={{
                  p: 3,
                  textAlign: 'center',
                  bgcolor: 'grey.50',
                  minHeight: 200,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Box>
                  <Typography variant="h3" sx={{ fontWeight: 700, color: 'success.main' }}>
                    {dashboardData?.new_users_this_month ?? 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    New Users
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {userMom !== undefined && userMom !== null
                      ? `${userMom >= 0 ? '+' : ''}${userMom.toFixed(1)}% growth rate`
                      : 'Growth trend unavailable'}
                  </Typography>
                </Box>
              </Paper>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ReportsPage;
