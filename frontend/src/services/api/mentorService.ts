import apiClient from './client';
import { MentorDetail } from '../../types';

export interface User {
  id: number;
  username: string;
  email: string;
  avatar: string;
  first_name: string;
  last_name: string;
}

export interface Mentor {
  id: number;
  user: User;
  bio: string;
  industry: string;
  current_position: string;
  years_of_experience: number;
  status: string;
  average_rating: number;
  total_reviews: number;
  total_sessions: number;
  total_earnings: number;
  is_verified: boolean;
  verification_badge: string;
  specializations: string[];
  ranking_score: number;
  is_approved: boolean;
  created_at: string;
  updated_at: string;
}

export interface MentorFilters {
  industry?: string;
  experience_level?: string;
  specialization?: string;
  search?: string;
}

const mentorService = {
  async getMentors(filters?: any): Promise<any[]> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v));
          } else {
            params.append(key, value.toString());
          }
        }
      });
    }
    const response = await apiClient.get<any[]>('/mentors/', { params });
    return response.data;
  },

  async getMentorById(id: number): Promise<MentorDetail> {
    const response = await apiClient.get<MentorDetail>(`/mentors/${id}/`);
    return response.data;
  },

  async getMentorAvailability(mentorId: number, date: string, serviceId?: number): Promise<any[]> {
    const params: any = { date };
    if (serviceId) {
      params.service_id = serviceId;
    }
    const response = await apiClient.get<any[]>(`/mentors/${mentorId}/availability/slots/`, {
      params
    });
    return response.data;
  },

  async getMentorServices(mentorId: number): Promise<any[]> {
    const response = await apiClient.get<any[]>(`/mentors/${mentorId}/services/`);
    return response.data;
  },

  async getMentorReviews(mentorId: number, page = 1): Promise<{
    reviews: Array<{
      id: number;
      rating: number;
      comment: string;
      created_at: string;
      user: {
        username: string;
        avatar: string;
      };
    }>;
    total: number;
    pages: number;
  }> {
    const response = await apiClient.get(`/mentors/${mentorId}/reviews/`, {
      params: { page }
    });
    return response.data;
  },
};

export default mentorService;