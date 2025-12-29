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
  Publish as PublishIcon,
  Unpublished as UnpublishIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../../components/common/LoadingSpinner';
import adminService from '../../../services/api/adminService';
import { useNotification } from '../../../components/common/NotificationProvider';

interface ContentItem {
  id: number;
  title: string;
  summary?: string;
  body?: string;
  cover_image_url?: string;
  type: 'blog' | 'resource' | 'guide';
  status: 'published' | 'draft' | 'archived';
  author: string;
  created_at: string;
  updated_at: string;
  views?: number;
}

const ContentManagementPage: React.FC = () => {
  const { showSuccess, showError } = useNotification();
  const [loading, setLoading] = useState(true);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingContent, setEditingContent] = useState<ContentItem | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    summary: '',
    body: '',
    cover_image_url: '',
    type: 'blog' as 'blog' | 'resource' | 'guide',
    status: 'draft' as 'published' | 'draft' | 'archived',
  });

  useEffect(() => {
    const fetchContent = async () => {
      try {
        const data = await adminService.getContent();
        const list = Array.isArray(data) ? data : (data?.results || []);
        const mapped = list.map((item: any) => ({
          id: item.id,
          title: item.title,
          summary: item.summary || '',
          body: item.body || '',
          cover_image_url: item.cover_image_url || '',
          type: item.content_type || item.type,
          status: item.status,
          author: item.author_name || item.author || 'Staff',
          created_at: item.created_at,
          updated_at: item.updated_at,
          views: item.views,
        }));
        setContent(mapped);
      } catch {
        showError('Failed to load content items.');
        setContent([]);
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [showError]);

  const handleOpenDialog = (item?: ContentItem) => {
    if (item) {
      setEditingContent(item);
      setFormData({
        title: item.title,
        summary: item.summary || '',
        body: item.body || '',
        cover_image_url: item.cover_image_url || '',
        type: item.type,
        status: item.status,
      });
    } else {
      setEditingContent(null);
      setFormData({
        title: '',
        summary: '',
        body: '',
        cover_image_url: '',
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
        const updated = await adminService.updateContent(editingContent.id, {
          title: formData.title,
          summary: formData.summary,
          body: formData.body,
          cover_image_url: formData.cover_image_url,
          content_type: formData.type,
          status: formData.status,
        });
        setContent(content.map(c =>
          c.id === editingContent.id
            ? {
                ...c,
                title: updated.title ?? formData.title,
                summary: updated.summary ?? formData.summary,
                body: updated.body ?? formData.body,
                cover_image_url: updated.cover_image_url ?? formData.cover_image_url,
                type: updated.content_type ?? formData.type,
                status: updated.status ?? formData.status,
                author: updated.author_name || c.author,
                updated_at: updated.updated_at || new Date().toISOString(),
                views: updated.views ?? c.views,
              }
            : c
        ));
        showSuccess('Content updated.');
      } else {
        const created = await adminService.createContent({
          title: formData.title,
          summary: formData.summary,
          body: formData.body,
          cover_image_url: formData.cover_image_url,
          content_type: formData.type,
          status: formData.status,
        });
        const newItem: ContentItem = {
          id: created.id,
          title: created.title ?? formData.title,
          summary: created.summary ?? formData.summary,
          body: created.body ?? formData.body,
          cover_image_url: created.cover_image_url ?? formData.cover_image_url,
          type: created.content_type ?? formData.type,
          status: created.status ?? formData.status,
          author: created.author_name || 'Staff',
          created_at: created.created_at || new Date().toISOString(),
          updated_at: created.updated_at || new Date().toISOString(),
          views: created.views,
        };
        setContent([newItem, ...content]);
        showSuccess('Content created.');
      }
      handleCloseDialog();
    } catch {
      showError('Failed to save content item.');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await adminService.deleteContent(id);
      setContent(content.filter(c => c.id !== id));
      showSuccess('Content deleted.');
    } catch {
      showError('Failed to delete content.');
    }
  };

  const handleTogglePublish = async (id: number) => {
    const target = content.find(c => c.id === id);
    if (!target) return;
    const nextStatus = target.status === 'published' ? 'draft' : 'published';
    try {
      const updated = await adminService.updateContent(id, {
        status: nextStatus,
      });
      setContent(content.map(c =>
        c.id === id
          ? { ...c, status: updated.status || nextStatus, updated_at: updated.updated_at || new Date().toISOString() }
          : c
      ));
      showSuccess(`Content ${nextStatus === 'published' ? 'published' : 'unpublished'}.`);
    } catch {
      showError('Failed to update content status.');
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
                        onClick={() => handleTogglePublish(item.id)}
                        color={item.status === 'published' ? 'warning' : 'success'}
                      >
                        {item.status === 'published' ? <UnpublishIcon /> : <PublishIcon />}
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
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Summary"
                value={formData.summary}
                onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                multiline
                minRows={2}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Body"
                value={formData.body}
                onChange={(e) => setFormData({ ...formData, body: e.target.value })}
                multiline
                minRows={4}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Cover Image URL"
                value={formData.cover_image_url}
                onChange={(e) => setFormData({ ...formData, cover_image_url: e.target.value })}
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

export default ContentManagementPage;
