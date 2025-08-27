import React, { ReactNode } from 'react';
import { Box, Container, ContainerProps } from '@mui/material';
import { useResponsive } from '../../hooks/useResponsive';

interface ResponsiveContainerProps extends Omit<ContainerProps, 'maxWidth'> {
  children: ReactNode;
  spacing?: number;
  disableGutters?: boolean;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false;
  minHeight?: string | number;
}

const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  spacing = 3,
  disableGutters = false,
  maxWidth = 'lg',
  minHeight,
  ...props
}) => {
  const { isMobile } = useResponsive();

  return (
    <Container
      maxWidth={maxWidth}
      disableGutters={disableGutters}
      {...props}
    >
      <Box
        sx={{
          py: isMobile ? spacing - 1 : spacing,
          px: disableGutters ? 0 : { xs: 2, sm: 3 },
          minHeight: minHeight,
        }}
      >
        {children}
      </Box>
    </Container>
  );
};

export default ResponsiveContainer;