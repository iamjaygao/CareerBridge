import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Chip,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';
import { SxProps, Theme } from '@mui/material/styles';

export interface AlertItem {
  id: string;
  type: 'warning' | 'error' | 'info' | 'success';
  title: string;
  description?: string;
  count?: number;
  actionLabel?: string;
  actionPath?: string;
  onClick?: () => void;
}

export interface AlertPanelProps {
  title: string;
  alerts: AlertItem[];
  onActionClick?: (alert: AlertItem) => void;
  emptyMessage?: string;
  maxItems?: number;
  sx?: SxProps<Theme>;
}

const AlertPanel: React.FC<AlertPanelProps> = ({
  title,
  alerts,
  onActionClick,
  emptyMessage = 'No alerts at this time',
  maxItems = 5,
  sx,
}) => {
  const getIcon = (type: AlertItem['type']) => {
    switch (type) {
      case 'error':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'info':
        return <InfoIcon color="info" />;
      case 'success':
        return <CheckCircleIcon color="success" />;
      default:
        return <InfoIcon />;
    }
  };

  const getColor = (type: AlertItem['type']) => {
    switch (type) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      case 'success':
        return 'success';
      default:
        return 'default';
    }
  };

  const displayedAlerts = alerts.slice(0, maxItems);
  const hasMore = alerts.length > maxItems;

  return (
    <Card
      sx={{
        border: '1px solid',
        borderColor: 'divider',
        ...sx,
      }}
    >
      <CardContent sx={{ p: 0 }}>
        <Box sx={{ p: 3, pb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {title}
            </Typography>
            {alerts.length > 0 && (
              <Chip
                label={alerts.length}
                color={alerts.some((a) => a.type === 'error' || a.type === 'warning') ? 'error' : 'default'}
                size="small"
                sx={{ fontWeight: 600 }}
              />
            )}
          </Box>
        </Box>

        <Divider />

        {displayedAlerts.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {emptyMessage}
            </Typography>
          </Box>
        ) : (
          <List sx={{ p: 0 }}>
            {displayedAlerts.map((alert, index) => (
              <React.Fragment key={alert.id}>
                <ListItem
                  sx={{
                    px: 3,
                    py: 2,
                    '&:hover': {
                      bgcolor: 'action.hover',
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 40 }}>{getIcon(alert.type)}</ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1" sx={{ fontWeight: 500 }}>
                          {alert.title}
                        </Typography>
                        {alert.count !== undefined && alert.count > 0 && (
                          <Chip
                            label={alert.count}
                            size="small"
                            color={getColor(alert.type)}
                            sx={{ height: 20, fontSize: '0.7rem' }}
                          />
                        )}
                      </Box>
                    }
                    secondary={alert.description}
                  />
                  {alert.actionLabel && (
                    <Button
                      size="small"
                      endIcon={<ArrowForwardIcon />}
                      onClick={() => {
                        if (alert.onClick) {
                          alert.onClick();
                        } else if (onActionClick) {
                          onActionClick(alert);
                        }
                      }}
                      sx={{ ml: 2 }}
                    >
                      {alert.actionLabel}
                    </Button>
                  )}
                </ListItem>
                {index < displayedAlerts.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}

        {hasMore && (
          <>
            <Divider />
            <Box sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                +{alerts.length - maxItems} more alerts
              </Typography>
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default AlertPanel;

