import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  LinearProgress,
  Alert,
  Card,
  CardContent,
} from '@mui/material';
import { CloudUpload as UploadIcon, ArrowBack } from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store';
import { uploadResume } from '../../store/slices/resumeSlice';
import PageHeader from '../../components/common/PageHeader';
import { useNotification } from '../../components/common/NotificationProvider';
import { getLandingPathByRole } from '../../utils/roleLanding';

const UploadResumePage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();
  const { showSuccess, showError } = useNotification();
  
  const { user } = useSelector((state: RootState) => state.auth);
  const uploadProgress = useSelector((state: RootState) => state.resumes.uploadProgress);
  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const basePath = user?.role === 'student' ? '/student/resumes' : '/resumes';
  const dashboardPath = getLandingPathByRole(user?.role);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      // Validate file type
      const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      if (!allowedTypes.includes(selectedFile.type)) {
        showError('Please select a valid file type (PDF, DOC, or DOCX)');
        return;
      }
      
      // Validate file size (max 10MB)
      if (selectedFile.size > 10 * 1024 * 1024) {
        showError('File size must be less than 10MB');
        return;
      }
      
      setFile(selectedFile);
      if (!title) {
        // Use file name without extension as default title
        setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''));
      }
    }
  };

  const handleSubmit = async () => {
    if (!file || !title.trim()) {
      showError('Please select a file and enter a title');
      return;
    }

    try {
      setIsUploading(true);
      await dispatch(uploadResume({ file, title: title.trim() })).unwrap();
      showSuccess('Resume uploaded successfully!');
      navigate(basePath);
    } catch (error) {
      showError('Failed to upload resume. Please try again.');
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      if (!allowedTypes.includes(droppedFile.type)) {
        showError('Please select a valid file type (PDF, DOC, or DOCX)');
        return;
      }
      
      if (droppedFile.size > 10 * 1024 * 1024) {
        showError('File size must be less than 10MB');
        return;
      }
      
      setFile(droppedFile);
      if (!title) {
        setTitle(droppedFile.name.replace(/\.[^/.]+$/, ''));
      }
    }
  };

  return (
    <>
      <PageHeader
        title="Upload Resume"
        breadcrumbs={[
          { label: 'Dashboard', path: dashboardPath },
          { label: 'Resumes', path: basePath },
          { label: 'Upload Resume', path: `${basePath}/upload` },
        ]}
      />

      <Container maxWidth="md">
        <Paper sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Button
              startIcon={<ArrowBack />}
              onClick={() => navigate(basePath)}
              sx={{ mr: 2 }}
            >
              Back to Resumes
            </Button>
            <Typography variant="h4" component="h1">
              Upload Your Resume
            </Typography>
          </Box>

          <Alert severity="info" sx={{ mb: 3 }}>
            Upload your resume to get AI-powered analysis and feedback. Supported formats: PDF, DOC, DOCX (max 10MB).
          </Alert>

          <Box sx={{ mb: 4 }}>
            <TextField
              fullWidth
              label="Resume Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              margin="normal"
              placeholder="e.g., Software Engineer Resume 2024"
              helperText="Give your resume a descriptive title for easy identification"
            />
          </Box>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept=".pdf,.doc,.docx"
            style={{ display: 'none' }}
          />

          <Card
            sx={{
              p: 4,
              border: '2px dashed',
              borderColor: file ? 'success.main' : 'primary.main',
              borderRadius: 2,
              textAlign: 'center',
              cursor: 'pointer',
              backgroundColor: file ? 'success.light' : 'background.paper',
              transition: 'all 0.3s ease',
              '&:hover': {
                borderColor: 'primary.dark',
                backgroundColor: 'action.hover',
              },
            }}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <CardContent>
              <UploadIcon 
                sx={{ 
                  fontSize: 64, 
                  color: file ? 'success.main' : 'primary.main', 
                  mb: 2 
                }} 
              />
              
              {file ? (
                <Box>
                  <Typography variant="h6" color="success.main" gutterBottom>
                    File Selected Successfully!
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {file.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Size: {(file.size / 1024 / 1024).toFixed(2)} MB
                  </Typography>
                </Box>
              ) : (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Click to select or drag a file here
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Supported formats: PDF, DOC, DOCX
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Maximum file size: 10MB
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>

          {uploadProgress !== null && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="body2" gutterBottom>
                Uploading: {uploadProgress}%
              </Typography>
              <LinearProgress variant="determinate" value={uploadProgress} />
            </Box>
          )}

          <Box sx={{ display: 'flex', gap: 2, mt: 4 }}>
            <Button
              variant="outlined"
              onClick={() => navigate(basePath)}
              disabled={isUploading}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              onClick={handleSubmit}
              disabled={!file || !title.trim() || isUploading}
              startIcon={<UploadIcon />}
            >
              {isUploading ? 'Uploading...' : 'Upload Resume'}
            </Button>
          </Box>
        </Paper>
      </Container>
    </>
  );
};

export default UploadResumePage; 
