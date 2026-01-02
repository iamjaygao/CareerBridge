import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Paper,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  ExpandMore as ExpandMoreIcon,
  Assignment as AssignmentIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import signalsService, {
  ATSSignal,
  HumanReviewTask,
  SignalsDashboardData,
  ReviewTasksData,
} from '../../services/api/signalsService';
import { getUserFacingErrorMessage, handleApiError, type ApiError } from '../../services/utils/errorHandler';

const SignalsDashboard: React.FC = () => {
  const { decisionSlotId } = useParams<{ decisionSlotId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<ApiError | null>(null);
  const [signalsData, setSignalsData] = useState<SignalsDashboardData | null>(null);
  const [reviewTasksData, setReviewTasksData] = useState<ReviewTasksData | null>(null);

  useEffect(() => {
    if (!decisionSlotId) {
      const simpleError: ApiError = { message: 'Decision Slot ID is required' };
      setApiError(simpleError);
      setError('Decision Slot ID is required');
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        setApiError(null);
        const data = await signalsService.getDashboardData(decisionSlotId);
        setSignalsData(data.signals);
        setReviewTasksData(data.reviewTasks);
      } catch (err) {
        const errorObj = handleApiError(err);
        setApiError(errorObj);
        setError(getUserFacingErrorMessage(err, 'An unexpected error occurred'));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [decisionSlotId]);

  const getSeverityColor = (severity: string): 'error' | 'warning' | 'info' | 'success' => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'info';
      default:
        return 'info';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'high':
        return <WarningIcon color="warning" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'warning' => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'primary';
      case 'pending':
        return 'warning';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    // If we have an apiError, use it; otherwise create a simple one from the error string
    const errorToShow = apiError || { message: error };
    return <ErrorAlert error={errorToShow} overrideMessage={error} />;
  }

  if (!signalsData && !reviewTasksData) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">No signals or review tasks found for this decision slot.</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        ATS Signals Dashboard
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Decision Slot ID: {decisionSlotId}
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        {/* Summary Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Signals
              </Typography>
              <Typography variant="h3" color="primary">
                {signalsData?.total_count || 0}
              </Typography>
              {signalsData && signalsData.critical_count > 0 && (
                <Chip
                  label={`${signalsData.critical_count} Critical`}
                  color="error"
                  size="small"
                  sx={{ mt: 1 }}
                />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Review Tasks
              </Typography>
              <Typography variant="h3" color="primary">
                {reviewTasksData?.total_count || 0}
              </Typography>
              {reviewTasksData && reviewTasksData.pending_count > 0 && (
                <Chip
                  label={`${reviewTasksData.pending_count} Pending`}
                  color="warning"
                  size="small"
                  sx={{ mt: 1 }}
                />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                High Priority
              </Typography>
              <Typography variant="h3" color="warning.main">
                {signalsData?.high_count || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Signals by Severity */}
        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom sx={{ mt: 2 }}>
            Signals by Severity
          </Typography>
        </Grid>

        {signalsData && (
          <>
            {/* Critical Signals */}
            {signalsData.grouped_by_severity.critical.length > 0 && (
              <Grid item xs={12}>
                <Paper sx={{ p: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
                  <Typography variant="h6" gutterBottom>
                    Critical Signals ({signalsData.grouped_by_severity.critical.length})
                  </Typography>
                  <List>
                    {signalsData.grouped_by_severity.critical.map((signal) => (
                      <ListItem key={signal.id} sx={{ bgcolor: 'background.paper', mb: 1, borderRadius: 1 }}>
                        <ListItemIcon>{getSeverityIcon(signal.severity)}</ListItemIcon>
                        <ListItemText
                          primary={signal.message}
                          secondary={
                            <>
                              <Typography variant="caption" display="block">
                                Type: {signal.signal_type} | Category: {signal.category}
                              </Typography>
                              {signal.section && (
                                <Typography variant="caption" display="block">
                                  Section: {signal.section}
                                  {signal.line_number && ` (Line ${signal.line_number})`}
                                </Typography>
                              )}
                              <Typography variant="caption" display="block">
                                Created: {formatDate(signal.created_at)}
                              </Typography>
                            </>
                          }
                        />
                        <Chip
                          label={signal.severity.toUpperCase()}
                          color={getSeverityColor(signal.severity)}
                          size="small"
                        />
                      </ListItem>
                    ))}
                  </List>
                </Paper>
              </Grid>
            )}

            {/* High Priority Signals */}
            {signalsData.grouped_by_severity.high.length > 0 && (
              <Grid item xs={12}>
                <Paper sx={{ p: 2, bgcolor: 'warning.light' }}>
                  <Typography variant="h6" gutterBottom>
                    High Priority Signals ({signalsData.grouped_by_severity.high.length})
                  </Typography>
                  <List>
                    {signalsData.grouped_by_severity.high.map((signal) => (
                      <ListItem key={signal.id} sx={{ bgcolor: 'background.paper', mb: 1, borderRadius: 1 }}>
                        <ListItemIcon>{getSeverityIcon(signal.severity)}</ListItemIcon>
                        <ListItemText
                          primary={signal.message}
                          secondary={
                            <>
                              <Typography variant="caption" display="block">
                                Type: {signal.signal_type} | Category: {signal.category}
                              </Typography>
                              {signal.section && (
                                <Typography variant="caption" display="block">
                                  Section: {signal.section}
                                </Typography>
                              )}
                              <Typography variant="caption" display="block">
                                Created: {formatDate(signal.created_at)}
                              </Typography>
                            </>
                          }
                        />
                        <Chip
                          label={signal.severity.toUpperCase()}
                          color={getSeverityColor(signal.severity)}
                          size="small"
                        />
                      </ListItem>
                    ))}
                  </List>
                </Paper>
              </Grid>
            )}

            {/* Medium, Low, Info Signals */}
            {[
              { severity: 'medium', label: 'Medium Priority' },
              { severity: 'low', label: 'Low Priority' },
              { severity: 'info', label: 'Informational' },
            ].map(({ severity, label }) => {
              const signals = signalsData.grouped_by_severity[severity as keyof typeof signalsData.grouped_by_severity];
              if (signals.length === 0) return null;

              return (
                <Grid item xs={12} key={severity}>
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="h6">
                        {label} Signals ({signals.length})
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <List>
                        {signals.map((signal) => (
                          <ListItem key={signal.id}>
                            <ListItemIcon>{getSeverityIcon(signal.severity)}</ListItemIcon>
                            <ListItemText
                              primary={signal.message}
                              secondary={
                                <>
                                  <Typography variant="caption" display="block">
                                    Type: {signal.signal_type} | Category: {signal.category}
                                  </Typography>
                                  <Typography variant="caption" display="block">
                                    Created: {formatDate(signal.created_at)}
                                  </Typography>
                                </>
                              }
                            />
                            <Chip
                              label={signal.severity.toUpperCase()}
                              color={getSeverityColor(signal.severity)}
                              size="small"
                            />
                          </ListItem>
                        ))}
                      </List>
                    </AccordionDetails>
                  </Accordion>
                </Grid>
              );
            })}
          </>
        )}

        {/* Review Tasks */}
        {reviewTasksData && reviewTasksData.review_tasks.length > 0 && (
          <>
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h5" gutterBottom>
                Human Review Tasks
              </Typography>
            </Grid>

            {reviewTasksData.review_tasks.map((task) => (
              <Grid item xs={12} key={task.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          <AssignmentIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                          {task.task_type}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Task ID: {task.id}
                        </Typography>
                      </Box>
                      <Box>
                        <Chip
                          label={task.status.toUpperCase()}
                          color={getStatusColor(task.status)}
                          size="small"
                          sx={{ mr: 1 }}
                        />
                        <Chip
                          label={task.priority.toUpperCase()}
                          color={task.priority === 'urgent' ? 'error' : 'default'}
                          size="small"
                        />
                      </Box>
                    </Box>

                    {task.signal && (
                      <Alert severity={task.signal.is_critical ? 'error' : 'warning'} sx={{ mb: 2 }}>
                        <Typography variant="subtitle2">Related Signal:</Typography>
                        <Typography variant="body2">{task.signal.message}</Typography>
                      </Alert>
                    )}

                    {task.assigned_to_user && (
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <PersonIcon sx={{ mr: 1, fontSize: 20 }} />
                        <Typography variant="body2">
                          Assigned to: {task.assigned_to_user.first_name || task.assigned_to_user.username}
                        </Typography>
                      </Box>
                    )}

                    {task.due_at && (
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <ScheduleIcon sx={{ mr: 1, fontSize: 20 }} />
                        <Typography variant="body2" color={task.is_overdue ? 'error' : 'text.secondary'}>
                          Due: {formatDate(task.due_at)}
                          {task.is_overdue && ' (Overdue)'}
                        </Typography>
                      </Box>
                    )}

                    {task.review_notes && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Review Notes:
                        </Typography>
                        <Typography variant="body2">{task.review_notes}</Typography>
                      </Box>
                    )}

                    {task.review_decision && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Decision:
                        </Typography>
                        <Chip label={task.review_decision} color="primary" size="small" />
                      </Box>
                    )}

                    {task.reviewed_at && (
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                        Reviewed: {formatDate(task.reviewed_at)}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </>
        )}
      </Grid>
    </Box>
  );
};

export default SignalsDashboard;

