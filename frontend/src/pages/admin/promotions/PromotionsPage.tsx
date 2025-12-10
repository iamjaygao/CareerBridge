import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ContentCopy as CopyIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../../components/common/LoadingSpinner';
import adminService from '../../../services/api/adminService';

interface Promotion {
  id: number;
  code: string;
  name: string;
  discount_type: 'percentage' | 'fixed';
  discount_value: number;
  start_date: string;
  end_date: string;
  status: 'active' | 'expired' | 'draft';
  usage_count: number;
  max_uses?: number;
}

const PromotionsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [promotions, setPromotions] = useState<Promotion[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPromotion, setEditingPromotion] = useState<Promotion | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    discount_type: 'percentage' as 'percentage' | 'fixed',
    discount_value: 0,
    start_date: '',
    end_date: '',
    max_uses: '',
  });

  useEffect(() => {
    const fetchPromotions = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await adminService.getPromotions();
        
        // Handle different response formats
        let promotionsList: Promotion[] = [];
        if (Array.isArray(data)) {
          promotionsList = data;
        } else if (data.results && Array.isArray(data.results)) {
          promotionsList = data.results;
        } else if (data.data && Array.isArray(data.data)) {
          promotionsList = data.data;
        }
        
        // Normalize promotion objects
        const normalizedPromotions = promotionsList.map((p: any) => ({
          id: p.id,
          code: p.code || '',
          name: p.name || p.title || '',
          discount_type: p.discount_type || 'percentage',
          discount_value: p.discount_value || p.discount_amount || 0,
          start_date: p.start_date || p.start || '',
          end_date: p.end_date || p.end || '',
          status: p.status || 'draft',
          usage_count: p.usage_count || p.used_count || 0,
          max_uses: p.max_uses || p.max_usage || undefined,
        }));
        
        setPromotions(normalizedPromotions);
      } catch (err: any) {
        const errorMessage = err?.response?.data?.detail 
          || err?.response?.data?.error
          || err?.message 
          || 'Failed to load promotions';
        setError(errorMessage);
        console.error('Failed to fetch promotions:', err);
        setPromotions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchPromotions();
  }, []);

  const handleOpenDialog = (promotion?: Promotion) => {
    if (promotion) {
      setEditingPromotion(promotion);
      setFormData({
        name: promotion.name,
        code: promotion.code,
        discount_type: promotion.discount_type,
        discount_value: promotion.discount_value,
        start_date: promotion.start_date,
        end_date: promotion.end_date,
        max_uses: promotion.max_uses?.toString() || '',
      });
    } else {
      setEditingPromotion(null);
      setFormData({
        name: '',
        code: '',
        discount_type: 'percentage',
        discount_value: 0,
        start_date: '',
        end_date: '',
        max_uses: '',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingPromotion(null);
  };

  const handleSave = async () => {
    try {
      const promotionData = {
        name: formData.name,
        code: formData.code,
        discount_type: formData.discount_type,
        discount_value: formData.discount_value,
        start_date: formData.start_date,
        end_date: formData.end_date,
        max_uses: formData.max_uses ? parseInt(formData.max_uses) : undefined,
      };

      if (editingPromotion) {
        await adminService.updatePromotion(editingPromotion.id, promotionData);
      } else {
        await adminService.createPromotion(promotionData);
      }
      
      // Refresh promotions list
      const data = await adminService.getPromotions();
      let promotionsList: Promotion[] = [];
      if (Array.isArray(data)) {
        promotionsList = data;
      } else if (data.results && Array.isArray(data.results)) {
        promotionsList = data.results;
      } else if (data.data && Array.isArray(data.data)) {
        promotionsList = data.data;
      }
      
      const normalizedPromotions = promotionsList.map((p: any) => ({
        id: p.id,
        code: p.code || '',
        name: p.name || p.title || '',
        discount_type: p.discount_type || 'percentage',
        discount_value: p.discount_value || p.discount_amount || 0,
        start_date: p.start_date || p.start || '',
        end_date: p.end_date || p.end || '',
        status: p.status || 'draft',
        usage_count: p.usage_count || p.used_count || 0,
        max_uses: p.max_uses || p.max_usage || undefined,
      }));
      
      setPromotions(normalizedPromotions);
      handleCloseDialog();
    } catch (err: any) {
      console.error('Failed to save promotion:', err);
      const errorMessage = err?.response?.data?.detail 
        || err?.response?.data?.error
        || err?.message 
        || 'Failed to save promotion';
      alert(errorMessage);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this promotion?')) {
      return;
    }

    try {
      await adminService.deletePromotion(id);
      
      // Refresh promotions list
      const data = await adminService.getPromotions();
      let promotionsList: Promotion[] = [];
      if (Array.isArray(data)) {
        promotionsList = data;
      } else if (data.results && Array.isArray(data.results)) {
        promotionsList = data.results;
      } else if (data.data && Array.isArray(data.data)) {
        promotionsList = data.data;
      }
      
      const normalizedPromotions = promotionsList.map((p: any) => ({
        id: p.id,
        code: p.code || '',
        name: p.name || p.title || '',
        discount_type: p.discount_type || 'percentage',
        discount_value: p.discount_value || p.discount_amount || 0,
        start_date: p.start_date || p.start || '',
        end_date: p.end_date || p.end || '',
        status: p.status || 'draft',
        usage_count: p.usage_count || p.used_count || 0,
        max_uses: p.max_uses || p.max_usage || undefined,
      }));
      
      setPromotions(normalizedPromotions);
    } catch (err: any) {
      console.error('Failed to delete promotion:', err);
      const errorMessage = err?.response?.data?.detail 
        || err?.response?.data?.error
        || err?.message 
        || 'Failed to delete promotion';
      alert(errorMessage);
    }
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
  };

  const getStatusChip = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      active: 'success',
      expired: 'error',
      draft: 'warning',
    };
    return <Chip label={status.charAt(0).toUpperCase() + status.slice(1)} color={colors[status] || 'default'} size="small" />;
  };

  if (loading) {
    return <LoadingSpinner message="Loading promotions..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            Promotions
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage discount codes and promotional campaigns
          </Typography>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
            },
          }}
        >
          Create Promotion
        </Button>
      </Box>

      {/* Promotions Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Code</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Discount</TableCell>
                  <TableCell>Period</TableCell>
                  <TableCell>Usage</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {promotions.map((promotion) => (
                  <TableRow key={promotion.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" fontWeight="medium" sx={{ fontFamily: 'monospace' }}>
                          {promotion.code}
                        </Typography>
                        <IconButton
                          size="small"
                          onClick={() => handleCopyCode(promotion.code)}
                          sx={{ p: 0.5 }}
                        >
                          <CopyIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    </TableCell>
                    <TableCell>{promotion.name}</TableCell>
                    <TableCell>
                      {promotion.discount_type === 'percentage' 
                        ? `${promotion.discount_value}%`
                        : `$${promotion.discount_value}`
                      }
                    </TableCell>
                    <TableCell>
                      {new Date(promotion.start_date).toLocaleDateString()} - {new Date(promotion.end_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {promotion.usage_count} {promotion.max_uses && `/ ${promotion.max_uses}`}
                    </TableCell>
                    <TableCell>
                      {getStatusChip(promotion.status)}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(promotion)}
                        color="primary"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(promotion.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingPromotion ? 'Edit Promotion' : 'Create New Promotion'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Promotion Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Promotion Code"
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                required
                sx={{ fontFamily: 'monospace' }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Discount Type</InputLabel>
                <Select
                  value={formData.discount_type}
                  label="Discount Type"
                  onChange={(e) => setFormData({ ...formData, discount_type: e.target.value as 'percentage' | 'fixed' })}
                >
                  <MenuItem value="percentage">Percentage</MenuItem>
                  <MenuItem value="fixed">Fixed Amount</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label={formData.discount_type === 'percentage' ? 'Discount %' : 'Discount Amount ($)'}
                value={formData.discount_value}
                onChange={(e) => setFormData({ ...formData, discount_value: parseFloat(e.target.value) || 0 })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="date"
                label="Start Date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="date"
                label="End Date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                type="number"
                label="Max Uses (optional)"
                value={formData.max_uses}
                onChange={(e) => setFormData({ ...formData, max_uses: e.target.value })}
                helperText="Leave empty for unlimited uses"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSave}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
              },
            }}
          >
            {editingPromotion ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PromotionsPage;

