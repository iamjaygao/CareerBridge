import apiClient from './client';

export interface Resume {
  id: number;
  title: string;
  file: string;
  status: string;
  created_at: string;
  analyzed_at?: string;
}

class ResumeService {
  /**
   * Get all resumes for the current user
   */
  async getResumes(): Promise<Resume[]> {
    try {
      const response = await apiClient.get('/resumes/');
      return response.data.results || response.data;
    } catch (error) {
      console.error('Failed to get resumes:', error);
      throw error;
    }
  }

  /**
   * Get a single resume by ID
   */
  async getResume(id: number): Promise<Resume> {
    try {
      const response = await apiClient.get(`/resumes/${id}/`);
      return response.data;
    } catch (error) {
      console.error('Failed to get resume:', error);
      throw error;
    }
  }

  /**
   * Upload a new resume
   */
  async uploadResume(file: File, title: string): Promise<Resume> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);

      const response = await apiClient.post('/resumes/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Failed to upload resume:', error);
      throw error;
    }
  }

  /**
   * Delete a resume
   */
  async deleteResume(id: number): Promise<void> {
    try {
      await apiClient.delete(`/resumes/${id}/`);
    } catch (error) {
      console.error('Failed to delete resume:', error);
      throw error;
    }
  }

  /**
   * Analyze a resume
   */
  async analyzeResume(id: number, industry?: string, jobTitle?: string): Promise<any> {
    try {
      const response = await apiClient.post(`/resumes/${id}/analyze/`, {
        industry,
        job_title: jobTitle,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to analyze resume:', error);
      throw error;
    }
  }

  /**
   * Get resume analysis results
   */
  async getResumeAnalysis(id: number): Promise<any> {
    try {
      const response = await apiClient.get(`/resumes/${id}/analysis/`);
      return response.data;
    } catch (error) {
      console.error('Failed to get resume analysis:', error);
      throw error;
    }
  }

  /**
   * Get analysis (alias for getResumeAnalysis)
   */
  async getAnalysis(id: number): Promise<any> {
    return this.getResumeAnalysis(id);
  }

  /**
   * Get resume feedback
   */
  async getFeedback(id: number): Promise<any> {
    try {
      const response = await apiClient.get(`/resumes/${id}/feedback/`);
      return response.data;
    } catch (error) {
      console.error('Failed to get resume feedback:', error);
      throw error;
    }
  }

  /**
   * Download resume file
   */
  async downloadResume(id: number): Promise<Blob> {
    try {
      const response = await apiClient.get(`/resumes/${id}/download/`, {
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      console.error('Failed to download resume:', error);
      throw error;
    }
  }
}

const resumeService = new ResumeService();
export default resumeService;

