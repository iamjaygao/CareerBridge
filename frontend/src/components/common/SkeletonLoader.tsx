import React from 'react';
import {
  Box,
  Skeleton,
  Card,
  CardContent,
  Grid,
} from '@mui/material';

interface SkeletonLoaderProps {
  type?: 'card' | 'list' | 'table' | 'chart' | 'profile';
  count?: number;
  height?: number;
  width?: number | string;
}

const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  type = 'card',
  count = 1,
  height,
  width,
}) => {
  const renderCardSkeleton = () => (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Skeleton variant="text" width="60%" height={32} sx={{ mb: 1 }} />
        <Skeleton variant="text" width="40%" height={24} sx={{ mb: 2 }} />
        <Skeleton variant="rectangular" height={120} sx={{ mb: 2 }} />
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Skeleton variant="text" width="30%" height={20} />
          <Skeleton variant="text" width="20%" height={20} />
        </Box>
      </CardContent>
    </Card>
  );

  const renderListSkeleton = () => (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Skeleton variant="circular" width={40} height={40} sx={{ mr: 2 }} />
        <Box sx={{ flex: 1 }}>
          <Skeleton variant="text" width="70%" height={24} />
          <Skeleton variant="text" width="50%" height={20} />
        </Box>
      </Box>
      <Skeleton variant="rectangular" height={1} />
    </Box>
  );

  const renderTableSkeleton = () => (
    <Box>
      <Box sx={{ display: 'flex', mb: 2 }}>
        <Skeleton variant="text" width="25%" height={32} sx={{ mr: 2 }} />
        <Skeleton variant="text" width="25%" height={32} sx={{ mr: 2 }} />
        <Skeleton variant="text" width="25%" height={32} sx={{ mr: 2 }} />
        <Skeleton variant="text" width="25%" height={32} />
      </Box>
      {Array.from({ length: 5 }).map((_, index) => (
        <Box key={index} sx={{ display: 'flex', mb: 1 }}>
          <Skeleton variant="text" width="25%" height={24} sx={{ mr: 2 }} />
          <Skeleton variant="text" width="25%" height={24} sx={{ mr: 2 }} />
          <Skeleton variant="text" width="25%" height={24} sx={{ mr: 2 }} />
          <Skeleton variant="text" width="25%" height={24} />
        </Box>
      ))}
    </Box>
  );

  const renderChartSkeleton = () => (
    <Box>
      <Skeleton variant="text" width="50%" height={32} sx={{ mb: 2 }} />
      <Skeleton variant="rectangular" height={300} sx={{ mb: 2 }} />
      <Box sx={{ display: 'flex', justifyContent: 'space-around' }}>
        <Skeleton variant="text" width="20%" height={20} />
        <Skeleton variant="text" width="20%" height={20} />
        <Skeleton variant="text" width="20%" height={20} />
        <Skeleton variant="text" width="20%" height={20} />
      </Box>
    </Box>
  );

  const renderProfileSkeleton = () => (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Skeleton variant="circular" width={80} height={80} sx={{ mr: 3 }} />
        <Box sx={{ flex: 1 }}>
          <Skeleton variant="text" width="60%" height={32} sx={{ mb: 1 }} />
          <Skeleton variant="text" width="40%" height={24} sx={{ mb: 1 }} />
          <Skeleton variant="text" width="80%" height={20} />
        </Box>
      </Box>
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Skeleton variant="rectangular" height={100} sx={{ mb: 2 }} />
          <Skeleton variant="text" width="100%" height={20} sx={{ mb: 1 }} />
          <Skeleton variant="text" width="80%" height={20} />
        </Grid>
        <Grid item xs={12} md={6}>
          <Skeleton variant="rectangular" height={100} sx={{ mb: 2 }} />
          <Skeleton variant="text" width="100%" height={20} sx={{ mb: 1 }} />
          <Skeleton variant="text" width="80%" height={20} />
        </Grid>
      </Grid>
    </Box>
  );

  const renderSkeleton = () => {
    switch (type) {
      case 'card':
        return renderCardSkeleton();
      case 'list':
        return renderListSkeleton();
      case 'table':
        return renderTableSkeleton();
      case 'chart':
        return renderChartSkeleton();
      case 'profile':
        return renderProfileSkeleton();
      default:
        return (
          <Skeleton
            variant="rectangular"
            height={height || 200}
            width={width || '100%'}
          />
        );
    }
  };

  return (
    <Box>
      {Array.from({ length: count }).map((_, index) => (
        <Box key={index}>
          {renderSkeleton()}
        </Box>
      ))}
    </Box>
  );
};

export default SkeletonLoader; 