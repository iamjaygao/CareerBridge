import React from 'react';
import { Card, CardContent, Box, Typography, Skeleton } from '@mui/material';
import { SxProps, Theme } from '@mui/material/styles';

export interface KPICardProps {
  title: string;
  value: number | string;
  icon?: React.ReactNode;
  subtitle?: string;
  trend?: {
    value: number;
    label: string;
  };
  loading?: boolean;
  onClick?: () => void;
  sx?: SxProps<Theme>;
}

const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  icon,
  subtitle,
  trend,
  loading = false,
  onClick,
  sx,
}) => {
  return (
    <Card
      onClick={onClick}
      sx={{
        height: '100%',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s ease-in-out',
        border: '1px solid',
        borderColor: 'divider',
        '&:hover': onClick
          ? {
              transform: 'translateY(-2px)',
              boxShadow: 3,
              borderColor: 'primary.main',
            }
          : {},
        ...sx,
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          {icon && (
            <Box
              sx={{
                p: 1.5,
                borderRadius: 2,
                bgcolor: 'primary.light',
                color: 'primary.main',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {icon}
            </Box>
          )}
          {trend && (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-end',
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  color: trend.value >= 0 ? 'success.main' : 'error.main',
                  fontWeight: 600,
                  fontSize: '0.75rem',
                }}
              >
                {trend.value >= 0 ? '+' : ''}
                {trend.value.toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                {trend.label}
              </Typography>
            </Box>
          )}
        </Box>

        {loading ? (
          <>
            <Skeleton variant="text" width="60%" height={40} sx={{ mb: 1 }} />
            <Skeleton variant="text" width="40%" height={24} />
          </>
        ) : (
          <>
            <Typography
              variant="h3"
              component="div"
              sx={{
                fontWeight: 700,
                mb: 0.5,
                color: 'text.primary',
                lineHeight: 1.2,
              }}
            >
              {typeof value === 'number' ? value.toLocaleString() : value}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                {subtitle}
              </Typography>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default KPICard;

