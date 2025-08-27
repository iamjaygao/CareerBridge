import React from 'react';
import { Grid, GridProps } from '@mui/material';

const ResponsiveGrid: React.FC<GridProps> = ({ children, ...props }) => (
  <Grid container {...props}>
    {children}
  </Grid>
);

export default ResponsiveGrid;