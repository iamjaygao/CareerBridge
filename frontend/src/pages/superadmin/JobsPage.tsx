import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import { PlayArrow as PlayIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { useRole } from '../../contexts/RoleContext';
import adminService from '../../services/api/adminService';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const JobsPage: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const { isSuperAdmin } = useRole();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({
    totalJobs: 0,
    activeCrawlers: 0,
    lastCrawl: '',
  });
  const [crawlerLogs, setCrawlerLogs] = useState<any[]>([]);

  useEffect(() => {
    const fetchJobStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await adminService.getJobStats();
        
        setStats({
          totalJobs: data.total_jobs || data.totalJobs || 0,
          activeCrawlers: data.active_crawlers || data.activeCrawlers || 0,
          lastCrawl: data.last_crawl || data.lastCrawl || 'Never',
        });
        
        const logs = data.crawler_logs || data.logs || [];
        setCrawlerLogs(Array.isArray(logs) ? logs : []);
      } catch (err: any) {
        const errorMessage = err?.response?.data?.detail 
          || err?.response?.data?.error
          || err?.message 
          || 'Failed to load job statistics';
        setError(errorMessage);
        console.error('Failed to fetch job stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchJobStats();
  }, []);

  const handleTriggerCrawler = async () => {
    try {
      await adminService.triggerCrawler();
      // Refresh stats after triggering
      const data = await adminService.getJobStats();
      setStats({
        totalJobs: data.total_jobs || data.totalJobs || 0,
        activeCrawlers: data.active_crawlers || data.activeCrawlers || 0,
        lastCrawl: data.last_crawl || data.lastCrawl || 'Never',
      });
      const logs = data.crawler_logs || data.logs || [];
      setCrawlerLogs(Array.isArray(logs) ? logs : []);
      alert('Crawler triggered successfully');
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail 
        || err?.response?.data?.error
        || err?.message 
        || 'Failed to trigger crawler';
      alert(errorMessage);
    }
  };

  const handleCleanExpired = async () => {
    if (!window.confirm('Are you sure you want to clean expired jobs?')) {
      return;
    }
    try {
      await adminService.cleanExpiredJobs();
      alert('Expired jobs cleaned successfully');
      // Refresh stats
      const data = await adminService.getJobStats();
      setStats({
        totalJobs: data.total_jobs || data.totalJobs || 0,
        activeCrawlers: data.active_crawlers || data.activeCrawlers || 0,
        lastCrawl: data.last_crawl || data.lastCrawl || 'Never',
      });
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail 
        || err?.response?.data?.error
        || err?.message 
        || 'Failed to clean expired jobs';
      alert(errorMessage);
    }
  };

  if (!isSuperAdmin) {
    return null;
  }

  if (loading) {
    return <LoadingSpinner message="Loading job statistics..." />;
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
          Market Intelligence Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage job crawler and market data
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Jobs
              </Typography>
              <Typography variant="h4">{stats.totalJobs}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Crawlers
              </Typography>
              <Typography variant="h4">{stats.activeCrawlers}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Last Crawl
              </Typography>
              <Typography variant="body1">{stats.lastCrawl}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Crawler Controls
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <Button variant="contained" startIcon={<PlayIcon />} onClick={handleTriggerCrawler}>
            Trigger Crawler
          </Button>
          <Button variant="outlined" color="error" startIcon={<DeleteIcon />} onClick={handleCleanExpired}>
            Clean Expired Jobs
          </Button>
        </Box>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Crawler Logs
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Timestamp</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Jobs Found</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {crawlerLogs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No crawler logs found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                crawlerLogs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>
                      {log.timestamp || log.created_at 
                        ? new Date(log.timestamp || log.created_at).toLocaleString()
                        : 'N/A'}
                    </TableCell>
                    <TableCell>
                      <Typography color={log.status === 'success' ? 'success.main' : 'error.main'}>
                        {log.status || 'unknown'}
                      </Typography>
                    </TableCell>
                    <TableCell>{log.jobs_found || log.jobsFound || 0}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Container>
  );
};

export default JobsPage;

