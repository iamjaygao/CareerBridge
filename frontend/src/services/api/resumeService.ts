import apiClient from './client';

export interface Resume {
  id: number;
  title: string;
  file: string;
  status: string;
  created_at: string;
  uploaded_at?: string;
  updated_at?: string;
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
  async analyzeResume(
    id: number,
    industry?: string,
    jobTitle?: string,
    consent: boolean = false,
    consentVersion: string = '1.0'
  ): Promise<any> {
    try {
      const response = await apiClient.post('/resumes/analyze/', {
        resume_id: id,
        industry,
        job_title: jobTitle,
        consent,
        consent_version: consentVersion,
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
   * Get job recommendations for a resume
   */
  async getJobRecommendations(resumeId: number, limit = 3): Promise<any[]> {
    try {
      const response = await apiClient.get('/resumes/recommendations/', {
        params: { resume_id: resumeId, limit },
      });
      return response.data.recommendations || response.data.results || response.data || [];
    } catch (error) {
      console.error('Failed to get job recommendations:', error);
      throw error;
    }
  }

  /**
   * Get trending jobs data
   */
  async getTrendingJobs(): Promise<any> {
    try {
      const response = await apiClient.get('/resumes/jobs/trending/');
      return response.data;
    } catch (error) {
      console.error('Failed to get trending jobs:', error);
      throw error;
    }
  }

  /**
   * Get salary market data
   */
  async getSalaryData(jobTitle: string, location?: string): Promise<any> {
    try {
      const response = await apiClient.get('/resumes/market/salary/', {
        params: { job_title: jobTitle, location },
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get salary data:', error);
      throw error;
    }
  }

  /**
   * Get market skill demand data
   */
  async getSkillDemand(jobTitle: string, location?: string): Promise<any> {
    try {
      const response = await apiClient.get('/resumes/market/skills/', {
        params: { job_title: jobTitle, location },
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get skill demand:', error);
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

  async getLegalDisclaimers(): Promise<any[]> {
    const response = await apiClient.get('/resumes/legal/disclaimers/');
    return response.data;
  }

  async getLegalDisclaimer(type: string): Promise<any> {
    const response = await apiClient.get(`/resumes/legal/disclaimers/${type}/`);
    return response.data;
  }

  async getConsents(): Promise<any> {
    const response = await apiClient.get('/resumes/legal/consent/');
    return response.data;
  }

  async grantConsent(payload: {
    consent_type?: string;
    consent_version?: string;
    disclaimer_types?: string[];
  }): Promise<any> {
    const response = await apiClient.post('/resumes/legal/consent/', payload);
    return response.data;
  }

  async revokeConsent(payload: { consent_type?: string; disclaimer_type?: string }): Promise<any> {
    const response = await apiClient.post('/resumes/legal/consent/revoke/', payload);
    return response.data;
  }

  async requestDataDeletion(): Promise<any> {
    const response = await apiClient.post('/resumes/data/deletion/request/');
    return response.data;
  }

  async listDataDeletionRequests(): Promise<any[]> {
    const response = await apiClient.get('/resumes/data/deletion/requests/');
    return response.data;
  }
}

const resumeService = new ResumeService();
export default resumeService;
