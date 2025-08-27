import apiClient from './client';

export interface Resume {
  id: number;
  title: string;
  file_type: string;
  file_size: number;
  status: 'uploaded' | 'analyzing' | 'analyzed' | 'failed';
  uploaded_at: string;
  file: string; // Django FileField URL
  analysis_result?: {
    skills: string[];
    experience: string[];
    education: string[];
    recommendations: string[];
  };
}

const resumeService = {
  async getResumes(): Promise<Resume[]> {
    const response = await apiClient.get<Resume[]>('/resumes/');
    return response.data;
  },

  async uploadResume(file: File, title?: string): Promise<Resume> {
    const formData = new FormData();
    formData.append('file', file);
    if (title) {
      formData.append('title', title);
    }

    const response = await apiClient.post<Resume>('/resumes/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async deleteResume(id: number): Promise<void> {
    await apiClient.delete(`/resumes/${id}/`);
  },

  async analyzeResume(id: number): Promise<Resume> {
    const response = await apiClient.post<Resume>(`/resumes/analyze/`, { resume_id: id });
    return response.data;
  },

  async downloadResume(id: number): Promise<Blob> {
    const response = await apiClient.get(`/resumes/${id}/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  async getAnalysis(id: number): Promise<any> {
    const response = await apiClient.get(`/resumes/analysis/${id}/`);
    return response.data;
  },

  async getFeedback(id: number): Promise<any> {
    const response = await apiClient.get(`/resumes/feedback/${id}/`);
    return response.data;
  },
};

export default resumeService;