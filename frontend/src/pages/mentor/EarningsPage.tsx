import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  Paper as ChartPaper,
} from '@mui/material';
import {
  AccountBalance as BalanceIcon,
  TrendingUp as TrendingUpIcon,
  AttachMoney as MoneyIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';

interface Payout {
  id: number;
  date: string;
  amount: number;
  status: 'pending' | 'completed' | 'processing';
}

const MentorEarningsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [earnings, setEarnings] = useState({
    currentBalance: 450.00,
    monthlyEarnings: 1250.00,
    totalEarnings: 8750.00,
  });
  const [payouts, setPayouts] = useState<Payout[]>([]);

  useEffect(() => {
    setTimeout(() => {
      setPayouts([
        {
          id: 1,
          date: '2025-01-15T10:00:00Z',
          amount: 800.00,
          status: 'completed',
        },
        {
          id: 2,
          date: '2025-01-01T10:00:00Z',
          amount: 950.00,
          status: 'completed',
        },
        {
          id: 3,
          date: '2025-01-20T10:00:00Z',
          amount: 450.00,
          status: 'pending',
        },
      ]);
      setLoading(false);
    }, 500);
  }, []);

  const getStatusChip = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      pending: 'warning',
      processing: 'info',
      completed: 'success',
    };
    return <Chip label={status.charAt(0).toUpperCase() + status.slice(1)} color={colors[status] || 'default'} size="small" />;
  };

  if (loading) {
    return <LoadingSpinner message="Loading earnings..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Earnings
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Track your earnings and payout history
        </Typography>
      </Box>

      {/* Earnings Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <BalanceIcon sx={{ color: 'primary.main', mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Current Balance
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                ${earnings.currentBalance.toFixed(2)}
              </Typography>
              <Button variant="outlined" size="small" sx={{ mt: 2 }}>
                Request Payout
              </Button>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUpIcon sx={{ color: 'success.main', mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  This Month's Earnings
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                ${earnings.monthlyEarnings.toFixed(2)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                +12% from last month
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <MoneyIcon sx={{ color: 'info.main', mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Total Earnings
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                ${earnings.totalEarnings.toFixed(2)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                All time
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Earnings Chart (Placeholder) */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            Earnings Trend
          </Typography>
          <ChartPaper
            variant="outlined"
            sx={{
              p: 4,
              textAlign: 'center',
              bgcolor: 'grey.50',
              minHeight: 300,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main', mb: 1 }}>
                Chart Placeholder
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Earnings visualization will be displayed here
              </Typography>
            </Box>
          </ChartPaper>
        </CardContent>
      </Card>

      {/* Payout History */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            Payout History
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Amount</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {payouts.map((payout) => (
                  <TableRow key={payout.id} hover>
                    <TableCell>
                      {new Date(payout.date).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        ${payout.amount.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {getStatusChip(payout.status)}
                    </TableCell>
                    <TableCell align="right">
                      <Button size="small" variant="outlined">
                        View Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default MentorEarningsPage;

