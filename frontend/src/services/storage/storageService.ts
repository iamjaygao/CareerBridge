export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface UploadResult {
  url: string;
  filename: string;
  size: number;
  mimeType: string;
  etag?: string;
}

export interface StorageConfig {
  bucket: string;
  region: string;
  endpoint?: string;
  maxFileSize: number; // in bytes
  allowedTypes: string[];
}

class StorageService {
  private baseURL = process.env.REACT_APP_API_URL || '/api/v1';
  private config: StorageConfig = {
    bucket: process.env.REACT_APP_S3_BUCKET || 'careerbridge-uploads',
    region: process.env.REACT_APP_S3_REGION || 'us-east-1',
    endpoint: process.env.REACT_APP_S3_ENDPOINT,
    maxFileSize: 10 * 1024 * 1024, // 10MB
    allowedTypes: ['image/*', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
  };

  // Upload file with progress tracking
  async uploadFile(
    file: File,
    folder: string = 'uploads',
    onProgress?: (progress: UploadProgress) => void
  ): Promise<UploadResult> {
    try {
      // Validate file
      this.validateFile(file);

      // Get presigned URL for upload
      const presignedUrl = await this.getPresignedUrl(file, folder);

      // Upload file to S3
      const uploadResult = await this.uploadToS3(file, presignedUrl, onProgress);

      // Register file in our system
      const registeredFile = await this.registerFile({
        filename: file.name,
        size: file.size,
        mimeType: file.type,
        url: uploadResult.url,
        folder,
        etag: uploadResult.etag,
      });

      return registeredFile;
    } catch (error) {
      console.error('File upload failed:', error);
      throw error;
    }
  }

  // Upload multiple files
  async uploadFiles(
    files: File[],
    folder: string = 'uploads',
    onProgress?: (fileIndex: number, progress: UploadProgress) => void
  ): Promise<UploadResult[]> {
    const results: UploadResult[] = [];

    for (let i = 0; i < files.length; i++) {
      try {
        const result = await this.uploadFile(
          files[i],
          folder,
          (progress) => onProgress?.(i, progress)
        );
        results.push(result);
      } catch (error) {
        console.error(`Failed to upload file ${files[i].name}:`, error);
        throw error;
      }
    }

    return results;
  }

  // Delete file
  async deleteFile(fileId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseURL}/storage/files/${fileId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete file');
      }
    } catch (error) {
      console.error('File deletion failed:', error);
      throw error;
    }
  }

  // Get file info
  async getFileInfo(fileId: string): Promise<UploadResult> {
    try {
      const response = await fetch(`${this.baseURL}/storage/files/${fileId}/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get file info');
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get file info:', error);
      throw error;
    }
  }

  // Get user's files
  async getUserFiles(folder?: string, limit: number = 50, offset: number = 0): Promise<UploadResult[]> {
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
      });

      if (folder) {
        params.append('folder', folder);
      }

      const response = await fetch(`${this.baseURL}/storage/files/?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get user files');
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get user files:', error);
      throw error;
    }
  }

  // Generate thumbnail for image
  async generateThumbnail(fileId: string, width: number = 200, height: number = 200): Promise<string> {
    try {
      const response = await fetch(`${this.baseURL}/storage/files/${fileId}/thumbnail/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          width,
          height,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate thumbnail');
      }

      const { thumbnail_url } = await response.json();
      return thumbnail_url;
    } catch (error) {
      console.error('Thumbnail generation failed:', error);
      throw error;
    }
  }

  // Get file download URL
  async getDownloadUrl(fileId: string, expiresIn: number = 3600): Promise<string> {
    try {
      const response = await fetch(`${this.baseURL}/storage/files/${fileId}/download/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          expires_in: expiresIn,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get download URL');
      }

      const { download_url } = await response.json();
      return download_url;
    } catch (error) {
      console.error('Failed to get download URL:', error);
      throw error;
    }
  }

  // Private methods
  private validateFile(file: File): void {
    // Check file size
    if (file.size > this.config.maxFileSize) {
      throw new Error(`File size exceeds maximum allowed size of ${this.config.maxFileSize / 1024 / 1024}MB`);
    }

    // Check file type
    const isAllowedType = this.config.allowedTypes.some(type => {
      if (type.endsWith('/*')) {
        return file.type.startsWith(type.slice(0, -1));
      }
      return file.type === type;
    });

    if (!isAllowedType) {
      throw new Error(`File type ${file.type} is not allowed`);
    }
  }

  private async getPresignedUrl(file: File, folder: string): Promise<string> {
    try {
      const response = await fetch(`${this.baseURL}/storage/presigned-url/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          filename: file.name,
          content_type: file.type,
          folder,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get presigned URL');
      }

      const { presigned_url } = await response.json();
      return presigned_url;
    } catch (error) {
      console.error('Failed to get presigned URL:', error);
      throw error;
    }
  }

  private async uploadToS3(
    file: File,
    presignedUrl: string,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<{ url: string; etag?: string }> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress: UploadProgress = {
            loaded: event.loaded,
            total: event.total,
            percentage: Math.round((event.loaded / event.total) * 100),
          };
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const etag = xhr.getResponseHeader('ETag')?.replace(/"/g, '');
          // Extract URL from presigned URL (remove query parameters)
          const url = presignedUrl.split('?')[0];
          resolve({ url, etag });
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'));
      });

      xhr.open('PUT', presignedUrl);
      xhr.setRequestHeader('Content-Type', file.type);
      xhr.send(file);
    });
  }

  private async registerFile(fileData: {
    filename: string;
    size: number;
    mimeType: string;
    url: string;
    folder: string;
    etag?: string;
  }): Promise<UploadResult> {
    try {
      const response = await fetch(`${this.baseURL}/storage/files/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(fileData),
      });

      if (!response.ok) {
        throw new Error('Failed to register file');
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to register file:', error);
      throw error;
    }
  }

  // Utility methods
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  getFileIcon(mimeType: string): string {
    if (mimeType.startsWith('image/')) return '🖼️';
    if (mimeType === 'application/pdf') return '📄';
    if (mimeType.includes('word')) return '📝';
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return '📊';
    if (mimeType.includes('powerpoint') || mimeType.includes('presentation')) return '📈';
    if (mimeType.includes('zip') || mimeType.includes('rar')) return '📦';
    return '📎';
  }
}

export default new StorageService(); 