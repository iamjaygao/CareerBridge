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
  Alert,
} from '@mui/material';
import { Refresh as RefreshIcon, Download as DownloadIcon } from '@mui/icons-material';

import adminService from '../../services/api/adminService';
import LoadingSpinner from '../../components/common/LoadingSpinner';

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
  const [error, setError] = useState<string | null>(null);
  const [exports, setExports] = useState<ExportItem[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

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
      setError(err?.response?.data?.error || 'Failed to load export requests.');
      setExports([]);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExports();
  }, [page]);

  const getStatusChip = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      pending: 'warning',
      processing: 'info',
      completed: 'success',
      failed: 'error',
    };
    return <Chip label={status} color={colors[status] || 'default'} size="small" />;
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
        <Button variant="outlined" startIcon={<RefreshIcon />} onClick={() => fetchExports(1)}>
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
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
                </TableRow>
              </TableHead>
              <TableBody>
                {exports.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
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
                      <TableCell>{getStatusChip(item.status)}</TableCell>
                      <TableCell>{item.record_count ?? '-'}</TableCell>
                      <TableCell>
                        {item.created_at ? new Date(item.created_at).toLocaleString() : 'N/A'}
                      </TableCell>
                      <TableCell>
                        {item.status === 'completed' && item.file_path ? (
                          <Button
                            size="small"
                            startIcon={<DownloadIcon />}
                            href={`/api/v1/adminpanel/exports/${item.id}/download/`}
                          >
                            Download
                          </Button>
                        ) : 'Not ready'}
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
