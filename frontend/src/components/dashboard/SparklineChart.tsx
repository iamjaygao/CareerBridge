import React from 'react';
import { Box, Typography, Card, CardContent, Skeleton } from '@mui/material';
import { SxProps, Theme } from '@mui/material/styles';
import { TrendDataPoint } from '../../types';

export interface SparklineChartProps {
  title: string;
  data: TrendDataPoint[];
  color?: string;
  height?: number;
  loading?: boolean;
  onClick?: () => void;
  sx?: SxProps<Theme>;
}

const SparklineChart: React.FC<SparklineChartProps> = ({
  title,
  data,
  color = '#667eea',
  height = 60,
  loading = false,
  onClick,
  sx,
}) => {
  if (loading || !data || data.length === 0) {
    return (
      <Card
        onClick={onClick}
        sx={{
          cursor: onClick ? 'pointer' : 'default',
          border: '1px solid',
          borderColor: 'divider',
          ...sx,
        }}
      >
        <CardContent sx={{ p: 2 }}>
          <Skeleton variant="text" width="40%" height={20} sx={{ mb: 2 }} />
          <Skeleton variant="rectangular" width="100%" height={height} />
        </CardContent>
      </Card>
    );
  }

  const values = data.map((d) => d.value);
  const maxValue = Math.max(...values, 1);
  const minValue = Math.min(...values, 0);
  const range = maxValue - minValue || 1;

  // Calculate total and change
  const total = values.reduce((sum, val) => sum + val, 0);
  const firstValue = values[0] || 0;
  const lastValue = values[values.length - 1] || 0;
  const change = firstValue > 0 ? ((lastValue - firstValue) / firstValue) * 100 : 0;

  return (
    <Card
      onClick={onClick}
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        border: '1px solid',
        borderColor: 'divider',
        transition: 'all 0.2s ease-in-out',
        '&:hover': onClick
          ? {
              transform: 'translateY(-2px)',
              boxShadow: 2,
              borderColor: 'primary.main',
            }
          : {},
        ...sx,
      }}
    >
      <CardContent sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
          <Typography variant="body2" sx={{ fontWeight: 500, color: 'text.secondary' }}>
            {title}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography
              variant="caption"
              sx={{
                color: change >= 0 ? 'success.main' : 'error.main',
                fontWeight: 600,
                fontSize: '0.7rem',
              }}
            >
              {change >= 0 ? '+' : ''}
              {change.toFixed(1)}%
            </Typography>
          </Box>
        </Box>

        {/* Sparkline */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'space-between',
            height,
            gap: 0.5,
          }}
        >
          {values.map((value, index) => {
            const normalizedHeight = ((value - minValue) / range) * 100;
            return (
              <Box
                key={index}
                sx={{
                  flex: 1,
                  bgcolor: color,
                  height: `${Math.max(normalizedHeight, 2)}%`,
                  minHeight: value > 0 ? '2px' : 0,
                  borderRadius: '2px 2px 0 0',
                  transition: 'height 0.3s ease',
                  opacity: 0.8,
                  '&:hover': {
                    opacity: 1,
                  },
                }}
                title={`${new Date(data[index].date).toLocaleDateString()}: ${value}`}
              />
            );
          })}
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
            Total: {total}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
            Avg: {(total / values.length).toFixed(1)}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default SparklineChart;

