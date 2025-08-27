import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
} from '@mui/material';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store';
import { uploadResume } from '../../store/slices/resumeSlice';
import FileUpload from '../common/FileUpload';

interface UploadResumeDialogProps {
  open: boolean;
  onClose: () => void;
}

const UploadResumeDialog: React.FC<UploadResumeDialogProps> = ({ open, onClose }) => {
  const dispatch = useDispatch<AppDispatch>();
  const uploadProgress = useSelector((state: RootState) => state.resumes.uploadProgress);
  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string>('');

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setUploading(false);
    setError('');
    if (!title) {
      // Use file name without extension as default title
      setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''));
    }
  };

  const handleSubmit = async () => {
    if (file) {
      try {
        setUploading(true);
        setError('');
        await dispatch(uploadResume({ file, title })).unwrap();
        setTimeout(() => {
          onClose();
          setTitle('');
          setFile(null);
          setUploading(false);
          setError('');
        }, 1000);
      } catch (error) {
        setError('Failed to upload resume. Please try again.');
        console.error('Upload failed:', error);
      } finally {
        setUploading(false);
      }
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Upload Resume</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          <TextField
            fullWidth
            label="Resume Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            margin="normal"
          />

          <Box sx={{ mt: 2 }}>
            <FileUpload
              onFileSelect={handleFileSelect}
              onFileRemove={() => setFile(null)}
              acceptedTypes={['.pdf', '.doc', '.docx']}
              maxSize={10 * 1024 * 1024} // 10MB
              currentFile={file}
              loading={uploading}
              error={error}
              uploadProgress={uploadProgress || 0}
              title="Upload Resume"
              subtitle="Click to select or drag a resume file here"
              buttonText="Choose File"
            />
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={!file || !title}
        >
          Upload
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default UploadResumeDialog;