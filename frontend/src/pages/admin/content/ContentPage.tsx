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
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../../components/common/LoadingSpinner';
import ErrorAlert from '../../../components/common/ErrorAlert';
import adminService from '../../../services/api/adminService';
import { handleApiError } from '../../../services/utils/errorHandler';
import type { ApiError } from '../../../services/utils/errorHandler';

interface ContentItem {
  id: number;
  title: string;
  type: 'blog' | 'resource' | 'guide';
  status: 'published' | 'draft' | 'archived';
  author: string;
  created_at: string;
  updated_at: string;
  views?: number;
}

const ContentPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingContent, setEditingContent] = useState<ContentItem | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    type: 'blog' as 'blog' | 'resource' | 'guide',
    status: 'draft' as 'published' | 'draft' | 'archived',
  });

  useEffect(() => {
    const fetchContent = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await adminService.getContent();
        
        // Handle different response formats
        let contentList: ContentItem[] = [];
        if (Array.isArray(data)) {
          contentList = data;
        } else if (data.results && Array.isArray(data.results)) {
          contentList = data.results;
        } else if (data.data && Array.isArray(data.data)) {
          contentList = data.data;
        }
        
        // Normalize content objects
        const normalizedContent = contentList.map((item: any) => ({
          id: item.id,
          title: item.title || '',
          type: item.type || 'blog',
          status: item.status || 'draft',
          author: item.author || item.author_name || 'Admin',
          created_at: item.created_at || new Date().toISOString(),
          updated_at: item.updated_at || item.created_at || new Date().toISOString(),
          views: item.views || item.view_count || 0,
        }));
        
        setContent(normalizedContent);
      } catch (err: any) {
        setError(handleApiError(err));
        console.error('Failed to fetch content:', err);
        setContent([]);
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, []);

  const handleOpenDialog = (item?: ContentItem) => {
    if (item) {
      setEditingContent(item);
      setFormData({
        title: item.title,
        type: item.type,
        status: item.status,
      });
    } else {
      setEditingContent(null);
      setFormData({
        title: '',
        type: 'blog',
        status: 'draft',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingContent(null);
  };

  const handleSave = async () => {
    try {
      if (editingContent) {
        await adminService.updateContent(editingContent.id, formData);
      } else {
        await adminService.createContent(formData);
      }
      
      // Refresh content list
      const data = await adminService.getContent();
      let contentList: ContentItem[] = [];
      if (Array.isArray(data)) {
        contentList = data;
      } else if (data.results && Array.isArray(data.results)) {
        contentList = data.results;
      } else if (data.data && Array.isArray(data.data)) {
        contentList = data.data;
      }
      
      const normalizedContent = contentList.map((item: any) => ({
        id: item.id,
        title: item.title || '',
        type: item.type || 'blog',
        status: item.status || 'draft',
        author: item.author || item.author_name || 'Admin',
        created_at: item.created_at || new Date().toISOString(),
        updated_at: item.updated_at || item.created_at || new Date().toISOString(),
        views: item.views || item.view_count || 0,
      }));
      
      setContent(normalizedContent);
      handleCloseDialog();
    } catch (err: any) {
      console.error('Failed to save content:', err);
      const errorMessage = err?.response?.data?.detail 
        || err?.response?.data?.error
        || err?.message 
        || 'Failed to save content';
      alert(errorMessage);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this content item?')) {
      return;
    }

    try {
      await adminService.deleteContent(id);
      
      // Refresh content list
      const data = await adminService.getContent();
      let contentList: ContentItem[] = [];
      if (Array.isArray(data)) {
        contentList = data;
      } else if (data.results && Array.isArray(data.results)) {
        contentList = data.results;
      } else if (data.data && Array.isArray(data.data)) {
        contentList = data.data;
      }
      
      const normalizedContent = contentList.map((item: any) => ({
        id: item.id,
        title: item.title || '',
        type: item.type || 'blog',
        status: item.status || 'draft',
        author: item.author || item.author_name || 'Admin',
        created_at: item.created_at || new Date().toISOString(),
        updated_at: item.updated_at || item.created_at || new Date().toISOString(),
        views: item.views || item.view_count || 0,
      }));
      
      setContent(normalizedContent);
    } catch (err: any) {
      console.error('Failed to delete content:', err);
      const errorMessage = err?.response?.data?.detail 
        || err?.response?.data?.error
        || err?.message 
        || 'Failed to delete content';
      alert(errorMessage);
    }
  };

  const getTypeChip = (type: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      blog: 'primary',
      resource: 'info',
      guide: 'success',
    };
    return <Chip label={type.charAt(0).toUpperCase() + type.slice(1)} color={colors[type] || 'default'} size="small" />;
  };

  const getStatusChip = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      published: 'success',
      draft: 'warning',
      archived: 'error',
    };
    return <Chip label={status.charAt(0).toUpperCase() + status.slice(1)} color={colors[status] || 'default'} size="small" />;
  };

  if (loading) {
    return <LoadingSpinner message="Loading content..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            Content Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage blog posts, resources, and guides
          </Typography>
        </Box>
      </Box>

      {error && (
        <ErrorAlert error={error} overrideMessage="Failed to load content." />
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
          Create Content
        </Button>
      </Box>

      {/* Content Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Title</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Author</TableCell>
                  <TableCell>Views</TableCell>
                  <TableCell>Last Updated</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {content.map((item) => (
                  <TableRow key={item.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {item.title}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {getTypeChip(item.type)}
                    </TableCell>
                    <TableCell>
                      {getStatusChip(item.status)}
                    </TableCell>
                    <TableCell>{item.author}</TableCell>
                    <TableCell>
                      {item.views !== undefined ? item.views.toLocaleString() : '-'}
                    </TableCell>
                    <TableCell>
                      {new Date(item.updated_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(item)}
                        color="primary"
                      >
                        <ViewIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(item)}
                        color="primary"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(item.id)}
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
          {editingContent ? 'Edit Content' : 'Create New Content'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  value={formData.type}
                  label="Type"
                  onChange={(e) => setFormData({ ...formData, type: e.target.value as 'blog' | 'resource' | 'guide' })}
                >
                  <MenuItem value="blog">Blog Post</MenuItem>
                  <MenuItem value="resource">Resource</MenuItem>
                  <MenuItem value="guide">Guide</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.status}
                  label="Status"
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as 'published' | 'draft' | 'archived' })}
                >
                  <MenuItem value="draft">Draft</MenuItem>
                  <MenuItem value="published">Published</MenuItem>
                  <MenuItem value="archived">Archived</MenuItem>
                </Select>
              </FormControl>
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
            {editingContent ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ContentPage;
