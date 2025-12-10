import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Paper,
} from '@mui/material';
import {
  AttachMoney as MoneyIcon,
  TrendingUp as TrendingUpIcon,
  AccountBalance as AccountBalanceIcon,
  Payment as PaymentIcon,
  ShowChart as ChartIcon,
} from '@mui/icons-material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface FinancialOverviewProps {
  revenueToday: number;
  totalRevenue: number;
  mentorEarnings: number;
  platformEarnings: number;
  pendingPayouts: number;
  revenueTrend?: { date: string; amount: number }[];
  earningsSplit?: { platform: number; mentor: number };
}

interface KpiCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  iconColor: string;
}

// KPI Card Component - No truncation, full text visible
const KpiCard: React.FC<KpiCardProps> = ({ title, value, icon, iconColor }) => {
  return (
    <Card
      sx={{
        bgcolor: 'white',
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        borderRadius: '12px',
        px: 3,
        py: 2,
        minWidth: '190px',
        height: '100%',
        display: 'flex',
        gap: 2,
        alignItems: 'center',
        transition: 'all 0.2s ease',
        '&:hover': {
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        },
      }}
    >
      <Box
        sx={{
          height: '40px',
          width: '40px',
          borderRadius: '8px',
          bgcolor: `${iconColor}15`,
          color: iconColor,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        {icon}
      </Box>
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          lineHeight: 1.25,
          flexGrow: 1,
          minWidth: 0,
        }}
      >
        <Typography
          component="span"
          sx={{
            fontSize: {
              xs: '1.125rem',  // text-lg
              md: '1.25rem',   // md:text-xl
            },
            fontWeight: 600, // font-semibold
            color: '#111827', // text-gray-900
            lineHeight: 1.25,
            mb: 0.25,
          }}
        >
          {value}
        </Typography>
        <Typography
          component="span"
          sx={{
            fontSize: {
              xs: '0.75rem',   // text-xs
              md: '0.875rem',  // md:text-sm
            },
            color: '#6b7280', // text-gray-500
            fontWeight: 400,
            lineHeight: 1.25,
            display: 'block',
          }}
        >
          {title}
        </Typography>
      </Box>
    </Card>
  );
};

const FinancialOverview: React.FC<FinancialOverviewProps> = ({
  revenueToday = 0,
  totalRevenue = 0,
  mentorEarnings = 0,
  platformEarnings = 0,
  pendingPayouts = 0,
  revenueTrend = [],
  earningsSplit,
}) => {
  const formatCurrency = (amount: number) => {
    try {
      const num = Number(amount) || 0;
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(num);
    } catch (error) {
      return '$0.00';
    }
  };

  const formatCurrencyCompact = (amount: number) => {
    if (!amount || isNaN(amount) || !isFinite(amount)) {
      return '$0';
    }
    if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(1)}k`;
    }
    return `$${Math.round(amount)}`;
  };

  const financialCards: KpiCardProps[] = [
    {
      title: 'Revenue Today',
      value: formatCurrency(revenueToday || 0),
      icon: <MoneyIcon sx={{ fontSize: 24 }} />,
      iconColor: '#10b981',
    },
    {
      title: 'Total Revenue',
      value: formatCurrency(totalRevenue || 0),
      icon: <TrendingUpIcon sx={{ fontSize: 24 }} />,
      iconColor: '#3b82f6',
    },
    {
      title: 'Mentor Earnings',
      value: formatCurrency(mentorEarnings || 0),
      icon: <AccountBalanceIcon sx={{ fontSize: 24 }} />,
      iconColor: '#f59e0b',
    },
    {
      title: 'Platform Earnings',
      value: formatCurrency(platformEarnings || 0),
      icon: <ChartIcon sx={{ fontSize: 24 }} />,
      iconColor: '#8b5cf6',
    },
    {
      title: 'Pending Payouts',
      value: formatCurrency(pendingPayouts || 0),
      icon: <PaymentIcon sx={{ fontSize: 24 }} />,
      iconColor: '#ef4444',
    },
  ];

  // Prepare chart data for Recharts
  const chartData = (revenueTrend || []).map((item) => {
    try {
      const date = item?.date ? new Date(item.date) : new Date();
      return {
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        revenue: item?.amount || 0,
        fullDate: item?.date || new Date().toISOString(),
      };
    } catch (error) {
      return {
        date: '',
        revenue: 0,
        fullDate: new Date().toISOString(),
      };
    }
  }).filter(item => item.revenue >= 0);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length && payload[0]) {
      try {
        const value = payload[0].value || 0;
        const fullDate = payload[0].payload?.fullDate;
        return (
          <Box
            sx={{
              bgcolor: 'white',
              border: '1px solid',
              borderColor: 'rgba(0, 0, 0, 0.1)',
              borderRadius: '8px',
              p: 1.5,
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
          >
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
              {formatCurrency(value)}
            </Typography>
            {fullDate && (
              <Typography variant="caption" sx={{ color: '#6b7280' }}>
                {new Date(fullDate).toLocaleDateString('en-US', {
                  month: 'long',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </Typography>
            )}
          </Box>
        );
      } catch (error) {
        return null;
      }
    }
    return null;
  };

  return (
    <Box sx={{ mb: 6, mt: 5 }}>
      {/* Section Header */}
      <Box sx={{ mb: 5 }}>
        <Typography
          variant="h5"
          component="h2"
          sx={{
            fontWeight: 700,
            fontSize: '1.5rem',
            color: 'text.primary',
            mb: 0.5,
          }}
        >
          Financial Overview
        </Typography>
      </Box>

      {/* KPI Cards Grid - grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 */}
      <Grid 
        container 
        spacing={2} 
        sx={{ 
          mb: 6,
          '& > .MuiGrid-item': {
            minWidth: '190px',
          },
        }}
      >
        {financialCards.map((card, index) => (
          <Grid 
            item 
            xs={12} 
            sm={6} 
            lg={3}
            xl={2.4}
            key={index}
            sx={{
              display: 'flex',
            }}
          >
            <KpiCard {...card} />
          </Grid>
        ))}
      </Grid>

      {/* Charts Section - grid grid-cols-1 lg:grid-cols-3 gap-6 */}
      <Grid container spacing={3}>
        {/* Revenue Trend Chart - spans 2 columns */}
        <Grid item xs={12} lg={8}>
          <Paper
            sx={{
              bgcolor: 'white',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
              borderRadius: '12px',
              p: 4,
              height: '100%',
              border: '1px solid',
              borderColor: 'rgba(0, 0, 0, 0.06)',
            }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                fontSize: '1.125rem', // text-lg
                mb: 3,
                color: 'text.primary',
              }}
            >
              Revenue Trend (Last 30 Days)
            </Typography>
            {chartData && chartData.length > 0 ? (
              <Box
                sx={{
                  width: '100%',
                  height: 300,
                }}
              >
                {(() => {
                  try {
                    return (
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart
                          data={chartData}
                          margin={{
                            top: 20,
                            right: 30,
                            left: 20,
                            bottom: 5,
                          }}
                        >
                          <CartesianGrid
                            strokeDasharray="3 3"
                            stroke="#e5e7eb"
                            opacity={0.3}
                            vertical={false}
                          />
                          <XAxis
                            dataKey="date"
                            tick={{ fontSize: 11, fill: '#6b7280' }}
                            tickLine={false}
                            axisLine={false}
                            interval="preserveStartEnd"
                          />
                          <YAxis
                            tick={{ fontSize: 11, fill: '#6b7280' }}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(v) => {
                              try {
                                return formatCurrencyCompact(Number(v) || 0);
                              } catch {
                                return '$0';
                              }
                            }}
                            width={60}
                          />
                          <Tooltip content={<CustomTooltip />} />
                          <Bar
                            dataKey="revenue"
                            fill="#2374e1"
                            barSize={20}
                            radius={[4, 4, 0, 0]}
                          >
                            {chartData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill="#2374e1" />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    );
                  } catch (error) {
                    console.error('Chart rendering error:', error);
                    return (
                      <Box
                        sx={{
                          height: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: '#6b7280',
                        }}
                      >
                        <Typography variant="body2">
                          Unable to render chart. Please refresh the page.
                        </Typography>
                      </Box>
                    );
                  }
                })()}
              </Box>
            ) : (
              <Box
                sx={{
                  height: 300,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#6b7280',
                }}
              >
                <Typography variant="body2">No revenue data available</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Earnings Split Card - spans 1 column */}
        <Grid item xs={12} lg={4}>
          <Paper
            sx={{
              bgcolor: 'white',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
              borderRadius: '12px',
              p: 4,
              height: '100%',
              border: '1px solid',
              borderColor: 'rgba(0, 0, 0, 0.06)',
            }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                fontSize: '1.125rem', // text-lg
                mb: 3,
                color: 'text.primary',
              }}
            >
              Earnings Split
            </Typography>
            {earningsSplit ? (
              <Box>
                {/* Platform Earnings */}
                <Box sx={{ mb: 4 }}>
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 1.5,
                    }}
                  >
                    <Typography
                      variant="body2"
                      sx={{
                        fontSize: '0.875rem',
                        fontWeight: 500,
                        color: '#6b7280',
                      }}
                    >
                      Platform
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        fontSize: '0.875rem',
                        fontWeight: 600,
                        color: 'text.primary',
                      }}
                    >
                      {formatCurrency(earningsSplit.platform)}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      width: '100%',
                      height: 24,
                      bgcolor: '#f3f4f6',
                      borderRadius: '6px',
                      overflow: 'hidden',
                    }}
                  >
                    <Box
                      sx={{
                        width: `${(earningsSplit.platform / (earningsSplit.platform + earningsSplit.mentor)) * 100}%`,
                        height: '100%',
                        bgcolor: '#2374e1',
                        transition: 'width 0.3s ease',
                      }}
                    />
                  </Box>
                </Box>

                {/* Mentor Earnings */}
                <Box sx={{ mb: 3 }}>
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 1.5,
                    }}
                  >
                    <Typography
                      variant="body2"
                      sx={{
                        fontSize: '0.875rem',
                        fontWeight: 500,
                        color: '#6b7280',
                      }}
                    >
                      Mentors
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        fontSize: '0.875rem',
                        fontWeight: 600,
                        color: 'text.primary',
                      }}
                    >
                      {formatCurrency(earningsSplit.mentor)}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      width: '100%',
                      height: 24,
                      bgcolor: '#f3f4f6',
                      borderRadius: '6px',
                      overflow: 'hidden',
                    }}
                  >
                    <Box
                      sx={{
                        width: `${(earningsSplit.mentor / (earningsSplit.platform + earningsSplit.mentor)) * 100}%`,
                        height: '100%',
                        bgcolor: '#f59e0b',
                        transition: 'width 0.3s ease',
                      }}
                    />
                  </Box>
                </Box>

                {/* Total */}
                <Box
                  sx={{
                    mt: 3,
                    pt: 3,
                    borderTop: '1px solid',
                    borderColor: '#e5e7eb',
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <Typography
                      variant="body1"
                      sx={{
                        fontWeight: 600,
                        fontSize: '1rem',
                        color: 'text.primary',
                      }}
                    >
                      Total
                    </Typography>
                    <Typography
                      variant="body1"
                      sx={{
                        fontWeight: 700,
                        fontSize: '1.125rem',
                        color: 'text.primary',
                      }}
                    >
                      {formatCurrency(earningsSplit.platform + earningsSplit.mentor)}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            ) : (
              <Box
                sx={{
                  height: 200,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#6b7280',
                }}
              >
                <Typography variant="body2">No earnings data available</Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default FinancialOverview;
