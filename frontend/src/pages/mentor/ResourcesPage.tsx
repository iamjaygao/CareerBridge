import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
} from '@mui/material';
import {
  MenuBook as HandbookIcon,
  VideoCall as InterviewIcon,
  Gavel as GuidelinesIcon,
  Description as DocsIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import apiClient from '../../services/api/client';
import { handleApiError } from '../../services/utils/errorHandler';
import type { ApiError } from '../../services/utils/errorHandler';

interface Resource {
  id: number;
  title: string;
  description: string;
  icon: React.ReactNode;
  url?: string;
}

const MentorResourcesPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [resources, setResources] = useState<Resource[]>([]);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    const fetchResources = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiClient.get('/adminpanel/content/public/', {
          params: { content_type: 'guide' },
        });
        const list = Array.isArray(response.data) ? response.data : (response.data?.results || []);
        const mapped = list.map((item: any, index: number) => {
          const description = item.summary || item.body || 'Resource details coming soon.';
          const trimmed = description.length > 180 ? `${description.slice(0, 177)}...` : description;
          const icons = [
            <HandbookIcon sx={{ fontSize: 40 }} key="handbook" />,
            <InterviewIcon sx={{ fontSize: 40 }} key="interview" />,
            <GuidelinesIcon sx={{ fontSize: 40 }} key="guidelines" />,
            <DocsIcon sx={{ fontSize: 40 }} key="docs" />,
          ];
          return {
            id: item.id,
            title: item.title,
            description: trimmed,
            icon: icons[index % icons.length],
            url: '',
          };
        });
        setResources(mapped);
      } catch (err: any) {
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };

    fetchResources();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading resources..." />;
  }

  if (error) {
    return <ErrorAlert error={error} />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Mentor Resources
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Helpful guides and resources to enhance your mentoring
        </Typography>
      </Box>

      {/* Resources Grid */}
      <Grid container spacing={3}>
        {resources.length === 0 ? (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  No published resources yet.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ) : (
          resources.map((resource) => (
          <Grid item xs={12} md={6} key={resource.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: 'primary.light',
                      color: 'primary.main',
                      mr: 2,
                    }}
                  >
                    {resource.icon}
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {resource.title}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {resource.description}
                </Typography>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => {
                    if (resource.url) {
                      window.open(resource.url, '_blank', 'noopener,noreferrer');
                    }
                  }}
                  disabled={!resource.url}
                >
                  {resource.url ? 'View Resource' : 'Coming Soon'}
                </Button>
                {!resource.url && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                    Resources are being finalized.
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
          ))
        )}
      </Grid>
    </Box>
  );
};

export default MentorResourcesPage;
