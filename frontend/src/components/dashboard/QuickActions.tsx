import React from 'react';
import { Box, Button, Card, CardContent, Typography, Grid } from '@mui/material';
import { SxProps, Theme } from '@mui/material/styles';

export interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  variant?: 'contained' | 'outlined' | 'text';
}

export interface QuickActionsProps {
  title?: string;
  actions: QuickAction[];
  columns?: number;
  sx?: SxProps<Theme>;
}

const QuickActions: React.FC<QuickActionsProps> = ({
  title = 'Quick Actions',
  actions,
  columns = 3,
  sx,
}) => {
  return (
    <Card
      sx={{
        border: '1px solid',
        borderColor: 'divider',
        ...sx,
      }}
    >
      <CardContent sx={{ p: 3 }}>
        {title && (
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            {title}
          </Typography>
        )}
        <Grid container spacing={2}>
          {actions.map((action) => (
            <Grid item xs={12} sm={6} md={12 / columns} key={action.id}>
              <Button
                fullWidth
                variant={action.variant || 'outlined'}
                color={action.color || 'primary'}
                startIcon={action.icon}
                onClick={action.onClick}
                sx={{
                  py: 1.5,
                  justifyContent: 'flex-start',
                  textTransform: 'none',
                  fontWeight: 500,
                }}
              >
                {action.label}
              </Button>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default QuickActions;

