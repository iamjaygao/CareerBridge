import React, { useState, useRef, useCallback } from 'react';
import {
  Box,
  Button,
  Typography,
  LinearProgress,
  Alert,
  Paper,
  IconButton,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Delete as DeleteIcon,
  FileUpload as FileUploadIcon,
} from '@mui/icons-material';

export interface FileUploadProps {
  onFileSelect: (file: File) => void;
  onFileRemove?: () => void;
  acceptedTypes?: string[];
  maxSize?: number; // in bytes
  maxFiles?: number;
  disabled?: boolean;
  loading?: boolean;
  error?: string;
  currentFile?: File | null;
  uploadProgress?: number;
  title?: string;
  subtitle?: string;
  buttonText?: string;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  onFileRemove,
  acceptedTypes = ['*/*'],
  maxSize = 5 * 1024 * 1024, // 5MB default
  maxFiles = 1,
  disabled = false,
  loading = false,
  error,
  currentFile,
  uploadProgress,
  title = 'Upload File',
  subtitle = 'Drag and drop a file here, or click to select',
  buttonText = 'Choose File',
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): string | null => {
    // Check file size
    if (file.size > maxSize) {
      return `File size must be less than ${(maxSize / 1024 / 1024).toFixed(1)}MB`;
    }

    // Check file type
    if (acceptedTypes.length > 0 && !acceptedTypes.includes('*/*')) {
      const isValidType = acceptedTypes.some(type => {
        if (type.endsWith('/*')) {
          return file.type.startsWith(type.replace('/*', ''));
        }
        return file.type === type;
      });
      
      if (!isValidType) {
        return `File type not supported. Accepted types: ${acceptedTypes.join(', ')}`;
      }
    }

    return null;
  }, [acceptedTypes, maxSize]);

  const handleFileSelect = useCallback((file: File) => {
    const error = validateFile(file);
    if (error) {
      setValidationError(error);
      return;
    }

    setValidationError(null);
    onFileSelect(file);
  }, [validateFile, onFileSelect]);

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragOver(false);

    const files = event.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleRemove = () => {
    if (onFileRemove) {
      onFileRemove();
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box>
      <input
        ref={fileInputRef}
        type="file"
        accept={acceptedTypes.join(',')}
        onChange={handleInputChange}
        style={{ display: 'none' }}
        disabled={disabled}
      />

      {currentFile ? (
        <Paper
          elevation={1}
          sx={{
            p: 2,
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 1,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
              <FileUploadIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" noWrap>
                  {currentFile.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {formatFileSize(currentFile.size)}
                </Typography>
              </Box>
            </Box>
            {onFileRemove && (
              <IconButton
                onClick={handleRemove}
                disabled={disabled || loading}
                size="small"
                color="error"
              >
                <DeleteIcon />
              </IconButton>
            )}
          </Box>
          
          {uploadProgress !== undefined && (
            <Box sx={{ mt: 1 }}>
              <LinearProgress
                variant="determinate"
                value={uploadProgress}
                sx={{ height: 4, borderRadius: 2 }}
              />
              <Typography variant="caption" color="text.secondary">
                {uploadProgress}% uploaded
              </Typography>
            </Box>
          )}
        </Paper>
      ) : (
        <Paper
          elevation={isDragOver ? 8 : 1}
          sx={{
            p: 3,
            border: '2px dashed',
            borderColor: isDragOver ? 'primary.main' : 'divider',
            borderRadius: 2,
            backgroundColor: isDragOver ? 'action.hover' : 'background.paper',
            transition: 'all 0.2s ease-in-out',
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: disabled ? 0.6 : 1,
          }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleClick}
        >
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
            }}
          >
            <CloudUploadIcon
              sx={{
                fontSize: 48,
                color: isDragOver ? 'primary.main' : 'text.secondary',
                mb: 2,
              }}
            />
            <Typography variant="h6" gutterBottom>
              {title}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {subtitle}
            </Typography>
            <Button
              variant="outlined"
              startIcon={<FileUploadIcon />}
              disabled={disabled || loading}
            >
              {buttonText}
            </Button>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
              Max file size: {formatFileSize(maxSize)}
            </Typography>
          </Box>
        </Paper>
      )}

      {(error || validationError) && (
        <Alert severity="error" sx={{ mt: 1 }}>
          {error || validationError}
        </Alert>
      )}
    </Box>
  );
};

export default FileUpload; 