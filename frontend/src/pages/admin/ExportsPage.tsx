import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Pagination,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Paper,
} from '@mui/material';
import { Refresh as RefreshIcon, Download as DownloadIcon } from '@mui/icons-material';

import adminService from '../../services/api/adminService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import { handleApiError } from '../../services/utils/errorHandler';
import type { ApiError } from '../../services/utils/errorHandler';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api/v1';

interface ExportItem {
  id: number;
  name: string;
  export_type: string;
  export_type_display?: string;
  format: string;
  format_display?: string;
  status: string;
  file_path?: string;
  file_size?: number;
  record_count?: number;
  error_message?: string;
  created_at?: string;
  completed_at?: string;
}

const ExportsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [exports, setExports] = useState<ExportItem[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [retryingId, setRetryingId] = useState<number | null>(null);

  const fetchExports = async (targetPage = page) => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminService.getDataExports({ page: targetPage });
      if (Array.isArray(data)) {
        setExports(data);
        setTotalPages(1);
      } else if (data?.results && Array.isArray(data.results)) {
        setExports(data.results);
        setTotalPages(data.total_pages || Math.ceil((data.count || 0) / (data.page_size || 10)) || 1);
      } else {
        setExports([]);
        setTotalPages(1);
      }
    } catch (err: any) {
      setError(handleApiError(err));
      setExports([]);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExports();
  }, [page]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchExports();
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, page]);

  const getStatusChip = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      pending: 'warning',
      processing: 'info',
      completed: 'success',
      failed: 'error',
    };
    return <Chip label={status} color={colors[status] || 'default'} size="small" />;
  };

  const handleRetry = async (exportId: number) => {
    try {
      setRetryingId(exportId);
      setError(null);
      await adminService.retryDataExport(exportId);
      await fetchExports();
    } catch (err: any) {
      setError(handleApiError(err));
    } finally {
      setRetryingId(null);
    }
  };

  if (loading && exports.length === 0) {
    return <LoadingSpinner message="Loading export requests..." />;
  }

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            Data Exports
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Track export requests and download completed files
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            onClick={() => setAutoRefresh((prev) => !prev)}
          >
            {autoRefresh ? 'Auto Refresh: On' : 'Auto Refresh: Off'}
          </Button>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={() => fetchExports(1)}>
            Refresh
          </Button>
        </Box>
      </Box>

      {error && (
        <ErrorAlert error={error} overrideMessage="Failed to load export requests." />
      )}

      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Format</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Records</TableCell>
                  <TableCell>Requested</TableCell>
                  <TableCell>File</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {exports.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No export requests yet.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  exports.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>{item.name}</TableCell>
                      <TableCell>{item.export_type_display || item.export_type}</TableCell>
                      <TableCell>{item.format_display || item.format}</TableCell>
                      <TableCell>
                        <Box>
                          {getStatusChip(item.status)}
                          {item.status === 'failed' && item.error_message && (
                            <Typography variant="caption" color="error" display="block">
                              {item.error_message}
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>{item.record_count ?? '-'}</TableCell>
                      <TableCell>
                        {item.created_at ? new Date(item.created_at).toLocaleString() : 'N/A'}
                      </TableCell>
                      <TableCell>
                        {item.status === 'completed' && item.file_path ? (
                          <Button
                            size="small"
                            startIcon={<DownloadIcon />}
                            href={`${API_BASE_URL}/adminpanel/exports/${item.id}/download/`}
                          >
                            Download
                          </Button>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Not ready
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {['failed', 'pending'].includes(item.status) ? (
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => handleRetry(item.id)}
                            disabled={retryingId === item.id}
                          >
                            {retryingId === item.id ? 'Retrying...' : 'Retry'}
                          </Button>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            —
                          </Typography>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_, value) => setPage(value)}
                color="primary"
              />
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default ExportsPage;
