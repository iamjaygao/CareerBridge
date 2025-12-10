import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import { Work as WorkIcon } from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import adminService from '../../services/api/adminService';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const JobsPage: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({
    totalJobs: 0,
    lastCrawl: '',
  });
  const [crawlerLogs, setCrawlerLogs] = useState<any[]>([]);

  useEffect(() => {
    const fetchJobStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await adminService.getJobStats();
        
        // Handle response format: could be { total_jobs, last_crawl, crawler_logs } or nested
        setStats({
          totalJobs: data.total_jobs || data.totalJobs || 0,
          lastCrawl: data.last_crawl || data.lastCrawl || 'Never',
        });
        
        // Handle crawler logs - could be array or nested in response
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

  if (loading) {
    return <LoadingSpinner message="Loading job statistics..." />;
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
          Market Intelligence (Read-Only)
        </Typography>
        <Typography variant="body1" color="text.secondary">
          View job crawler results and market data
        </Typography>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        Admin has read-only access to market intelligence data. Only SuperAdmin can trigger crawler and modify configuration.
      </Alert>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Jobs
              </Typography>
              <Typography variant="h4">{stats.totalJobs}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
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

      <Paper>
        <Typography variant="h6" gutterBottom sx={{ p: 2 }}>
          Crawler Logs (Read-Only)
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
              {crawlerLogs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell>{log.timestamp}</TableCell>
                  <TableCell>
                    <Typography color={log.status === 'success' ? 'success.main' : 'error.main'}>
                      {log.status}
                    </Typography>
                  </TableCell>
                  <TableCell>{log.jobsFound}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Container>
  );
};

export default JobsPage;

