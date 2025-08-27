import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Paper,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
} from '@mui/icons-material';

export interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
}

export interface MetricCard {
  title: string;
  value: string | number;
  change?: number;
  changeType?: 'increase' | 'decrease' | 'neutral';
  icon?: React.ReactNode;
  color?: string;
  subtitle?: string;
}

export interface ProgressData {
  label: string;
  value: number;
  maxValue: number;
  color?: string;
  subtitle?: string;
}

interface DataVisualizationProps {
  metrics?: MetricCard[];
  chartData?: ChartDataPoint[];
  progressData?: ProgressData[];
  title?: string;
  subtitle?: string;
}

const DataVisualization: React.FC<DataVisualizationProps> = ({
  metrics = [],
  chartData = [],
  progressData = [],
  title,
  subtitle,
}) => {
  const getTrendIcon = (changeType?: 'increase' | 'decrease' | 'neutral') => {
    switch (changeType) {
      case 'increase':
        return <TrendingUpIcon color="success" />;
      case 'decrease':
        return <TrendingDownIcon color="error" />;
      case 'neutral':
        return <TrendingFlatIcon color="action" />;
      default:
        return null;
    }
  };

  const getTrendColor = (changeType?: 'increase' | 'decrease' | 'neutral') => {
    switch (changeType) {
      case 'increase':
        return 'success.main';
      case 'decrease':
        return 'error.main';
      case 'neutral':
        return 'text.secondary';
      default:
        return 'text.secondary';
    }
  };

  const formatValue = (value: string | number) => {
    if (typeof value === 'number') {
      if (value >= 1000000) {
        return `${(value / 1000000).toFixed(1)}M`;
      } else if (value >= 1000) {
        return `${(value / 1000).toFixed(1)}K`;
      }
      return value.toLocaleString();
    }
    return value;
  };

  const renderMetricCard = (metric: MetricCard) => (
    <Card key={metric.title} sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {metric.title}
          </Typography>
          {metric.icon && (
            <Box sx={{ color: metric.color || 'primary.main' }}>
              {metric.icon}
            </Box>
          )}
        </Box>
        
        <Typography variant="h4" component="div" gutterBottom>
          {formatValue(metric.value)}
        </Typography>
        
        {metric.subtitle && (
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {metric.subtitle}
          </Typography>
        )}
        
        {metric.change !== undefined && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {getTrendIcon(metric.changeType)}
            <Typography
              variant="body2"
              sx={{ color: getTrendColor(metric.changeType) }}
            >
              {metric.change > 0 ? '+' : ''}{metric.change}%
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const renderSimpleChart = (data: ChartDataPoint[]) => {
    const maxValue = Math.max(...data.map(d => d.value));
    
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Chart Overview
          </Typography>
          <Box sx={{ mt: 2 }}>
            {data.map((point, index) => (
              <Box key={index} sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">{point.label}</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {formatValue(point.value)}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={(point.value / maxValue) * 100}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: 'grey.200',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: point.color || 'primary.main',
                    },
                  }}
                />
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>
    );
  };

  const renderProgressSection = (data: ProgressData[]) => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Progress Overview
        </Typography>
        <Box sx={{ mt: 2 }}>
          {data.map((item, index) => (
            <Box key={index} sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">{item.label}</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {item.value} / {item.maxValue}
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={(item.value / item.maxValue) * 100}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: 'grey.200',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: item.color || 'primary.main',
                  },
                }}
              />
              {item.subtitle && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  {item.subtitle}
                </Typography>
              )}
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );

  const renderSummaryStats = () => {
    if (!chartData.length) return null;

    const total = chartData.reduce((sum, point) => sum + point.value, 0);
    const average = total / chartData.length;
    const max = Math.max(...chartData.map(d => d.value));
    const min = Math.min(...chartData.map(d => d.value));

    return (
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="primary">
              {formatValue(total)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Total
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="primary">
              {formatValue(average)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Average
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="success.main">
              {formatValue(max)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Maximum
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="error.main">
              {formatValue(min)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Minimum
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    );
  };

  return (
    <Box>
      {title && (
        <Typography variant="h5" gutterBottom>
          {title}
        </Typography>
      )}
      
      {subtitle && (
        <Typography variant="body1" color="text.secondary" gutterBottom>
          {subtitle}
        </Typography>
      )}

      {/* Metrics Cards */}
      {metrics.length > 0 && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {metrics.map(renderMetricCard)}
        </Grid>
      )}

      {/* Summary Stats */}
      {chartData.length > 0 && renderSummaryStats()}

      {/* Charts and Progress */}
      <Grid container spacing={3}>
        {chartData.length > 0 && (
          <Grid item xs={12} md={6}>
            {renderSimpleChart(chartData)}
          </Grid>
        )}
        
        {progressData.length > 0 && (
          <Grid item xs={12} md={6}>
            {renderProgressSection(progressData)}
          </Grid>
        )}
      </Grid>

      {/* Data Points as Chips */}
      {chartData.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Data Points
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {chartData.map((point, index) => (
              <Chip
                key={index}
                label={`${point.label}: ${formatValue(point.value)}`}
                color="primary"
                variant="outlined"
                sx={{
                  borderColor: point.color || 'primary.main',
                  color: point.color || 'primary.main',
                }}
              />
            ))}
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default DataVisualization; 