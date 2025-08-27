import React from 'react';
import { Box, Typography, Breadcrumbs, Link } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { BreadcrumbItem } from '../../types';

interface PageHeaderProps {
  title: string;
  breadcrumbs?: BreadcrumbItem[];
  action?: React.ReactNode;
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, breadcrumbs, action }) => {
  return (
    <Box sx={{ mb: 4 }}>
      {breadcrumbs && (
        <Breadcrumbs sx={{ mb: 2 }}>
          {breadcrumbs.map((item, index) => {
            const isLast = index === breadcrumbs.length - 1;
            return isLast ? (
              <Typography key={item.label} color="text.primary">
                {item.label}
              </Typography>
            ) : (
              <Link
                key={item.label}
                component={RouterLink}
                to={item.path || '#'}
                color="inherit"
              >
                {item.label}
              </Link>
            );
          })}
        </Breadcrumbs>
      )}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h4" component="h1" gutterBottom>
          {title}
        </Typography>
        {action && <Box>{action}</Box>}
      </Box>
    </Box>
  );
};

export default PageHeader;