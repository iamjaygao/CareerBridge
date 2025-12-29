import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PageHeader from '../../components/common/PageHeader';
import ResponsiveContainer from '../../components/common/ResponsiveContainer';
import resumeService from '../../services/api/resumeService';
import { useAuth } from '../../contexts/AuthContext';
import ForbiddenPage from '../error/ForbiddenPage';

interface DataConsent {
  id: number;
  consent_type: string;
  is_granted: boolean;
  granted_at?: string;
  revoked_at?: string;
  consent_version?: string;
}

interface LegalDisclaimer {
  id: number;
  disclaimer_type: string;
  title: string;
  content: string;
  version: string;
  effective_date: string;
  requires_consent: boolean;
}

interface DisclaimerConsent {
  id: number;
  disclaimer: LegalDisclaimer;
  consented_at: string;
}

interface DeletionRequest {
  id: number;
  status: string;
  requested_at: string;
  verified_at?: string;
  processed_at?: string;
}

const ConsentManagementPage: React.FC = () => {
  const { user, loading: authLoading } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataConsents, setDataConsents] = useState<DataConsent[]>([]);
  const [disclaimerConsents, setDisclaimerConsents] = useState<DisclaimerConsent[]>([]);
  const [requiredDisclaimers, setRequiredDisclaimers] = useState<LegalDisclaimer[]>([]);
  const [activeDisclaimers, setActiveDisclaimers] = useState<LegalDisclaimer[]>([]);
  const [deletionRequests, setDeletionRequests] = useState<DeletionRequest[]>([]);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [consents, disclaimers, deletions] = await Promise.all([
        resumeService.getConsents(),
        resumeService.getLegalDisclaimers(),
        resumeService.listDataDeletionRequests(),
      ]);
      setDataConsents(consents.data_consents || []);
      setDisclaimerConsents(consents.disclaimer_consents || []);
      setRequiredDisclaimers(consents.required_disclaimers || []);
      setActiveDisclaimers(disclaimers || []);
      setDeletionRequests(deletions || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to load consent data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === 'student') {
      loadData();
    }
  }, [user]);

  if (authLoading) {
    return <CircularProgress />;
  }

  if (!user || user.role !== 'student') {
    return <ForbiddenPage />;
  }

  const dataProcessingConsent = dataConsents.find((item) => item.consent_type === 'data_processing');

  const handleGrantConsent = async () => {
    setActionMsg(null);
    try {
      await resumeService.grantConsent({
        consent_type: 'data_processing',
        consent_version: '1.0',
        disclaimer_types: requiredDisclaimers.map((item) => item.disclaimer_type),
      });
      setActionMsg('Consent granted successfully.');
      await loadData();
    } catch (err: any) {
      setActionMsg(err?.message || 'Failed to grant consent.');
    }
  };

  const handleRevokeDataConsent = async () => {
    setActionMsg(null);
    try {
      await resumeService.revokeConsent({ consent_type: 'data_processing' });
      setActionMsg('Data processing consent revoked.');
      await loadData();
    } catch (err: any) {
      setActionMsg(err?.message || 'Failed to revoke consent.');
    }
  };

  const handleRevokeDisclaimer = async (disclaimerType: string) => {
    setActionMsg(null);
    try {
      await resumeService.revokeConsent({ disclaimer_type: disclaimerType });
      setActionMsg('Disclaimer consent revoked.');
      await loadData();
    } catch (err: any) {
      setActionMsg(err?.message || 'Failed to revoke disclaimer consent.');
    }
  };

  const handleRequestDeletion = async () => {
    setActionMsg(null);
    try {
      const result = await resumeService.requestDataDeletion();
      setActionMsg(`Deletion request created. Token: ${result.token}`);
      await loadData();
    } catch (err: any) {
      setActionMsg(err?.message || 'Failed to request deletion.');
    }
  };

  if (loading) {
    return <CircularProgress />;
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <ResponsiveContainer>
      <PageHeader
        title="Consent Management"
        breadcrumbs={[{ label: 'Settings', path: '/settings' }, { label: 'Consent', path: '/settings/consent' }]}
      />

      {actionMsg && <Alert severity="info" sx={{ mb: 2 }}>{actionMsg}</Alert>}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Data Processing Consent</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Required for AI analysis and resume assessment.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <Chip
              label={dataProcessingConsent?.is_granted ? 'Granted' : 'Not Granted'}
              color={dataProcessingConsent?.is_granted ? 'success' : 'warning'}
            />
            {dataProcessingConsent?.consent_version && (
              <Chip label={`Version ${dataProcessingConsent.consent_version}`} variant="outlined" />
            )}
          </Box>
          <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
            <Button variant="contained" onClick={handleGrantConsent}>
              Grant Consent
            </Button>
            <Button variant="outlined" color="warning" onClick={handleRevokeDataConsent}>
              Revoke Consent
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Required Disclaimers</Typography>
          {requiredDisclaimers.length === 0 ? (
            <Typography variant="body2" color="text.secondary">No outstanding disclaimers.</Typography>
          ) : (
            requiredDisclaimers.map((disclaimer) => (
              <Accordion key={disclaimer.id}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>{disclaimer.title} (v{disclaimer.version})</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>{disclaimer.content}</Typography>
                </AccordionDetails>
              </Accordion>
            ))
          )}
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Disclaimer Consents</Typography>
          {activeDisclaimers.length === 0 ? (
            <Typography variant="body2" color="text.secondary">No disclaimers available.</Typography>
          ) : (
            <List>
              {activeDisclaimers.map((disclaimer) => {
                const consented = disclaimerConsents.find(
                  (item) => item.disclaimer.disclaimer_type === disclaimer.disclaimer_type
                );
                return (
                  <ListItem key={disclaimer.id} divider>
                    <ListItemText
                      primary={`${disclaimer.title} (v${disclaimer.version})`}
                      secondary={consented ? `Consented at ${new Date(consented.consented_at).toLocaleString()}` : 'Not consented'}
                    />
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => handleRevokeDisclaimer(disclaimer.disclaimer_type)}
                      disabled={!consented}
                    >
                      Revoke
                    </Button>
                  </ListItem>
                );
              })}
            </List>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Data Deletion Requests</Typography>
          <Box sx={{ mb: 2 }}>
            <Button variant="outlined" onClick={handleRequestDeletion}>
              Request Deletion
            </Button>
          </Box>
          {deletionRequests.length === 0 ? (
            <Typography variant="body2" color="text.secondary">No deletion requests found.</Typography>
          ) : (
            <List>
              {deletionRequests.map((request) => (
                <ListItem key={request.id} divider>
                  <ListItemText
                    primary={`Request #${request.id}`}
                    secondary={`Status: ${request.status} • Requested: ${new Date(request.requested_at).toLocaleString()}`}
                  />
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>
    </ResponsiveContainer>
  );
};

export default ConsentManagementPage;
