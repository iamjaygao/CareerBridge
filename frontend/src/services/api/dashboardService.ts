import apiClient from './client';

export interface DashboardStats {
  totalResumes: number;
  totalAppointments: number;
  upcomingAppointments: number;
  completedSessions: number;
  resumeAnalysisCount: number;
  averageResumeScore: number;
  resumesUploaded?: number;
  mentorSessions?: number;
  profileViews?: number;
}

export interface RecentActivity {
  id: number;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  link?: string;
}

class DashboardService {
  /**
   * Get dashboard statistics
   */
  async getDashboardStats(): Promise<DashboardStats> {
    try {
      const response = await apiClient.get('/users/dashboard/stats/');
      if (response.data?.stats) {
        return response.data.stats;
      }
      return response.data;
    } catch (error) {
      console.error('Failed to get dashboard stats:', error);
      // Return default stats if API fails
      return {
        totalResumes: 0,
        totalAppointments: 0,
        upcomingAppointments: 0,
        completedSessions: 0,
        resumeAnalysisCount: 0,
        averageResumeScore: 0,
      };
    }
  }

  /**
   * Get dashboard data (alias for getDashboardStats)
   */
  async getDashboardData(): Promise<DashboardStats> {
    return this.getDashboardStats();
  }

  /**
   * Get recent activities
   */
  async getRecentActivities(limit: number = 10): Promise<RecentActivity[]> {
    try {
      const response = await apiClient.get('/users/dashboard/stats/');
      const activities = response.data?.activities || [];
      return activities.slice(0, limit);
    } catch (error) {
      console.error('Failed to get recent activities:', error);
      return [];
    }
  }

  /**
   * Get upcoming appointments
   */
  async getUpcomingAppointments(limit: number = 5): Promise<any[]> {
    try {
      const response = await apiClient.get('/appointments/appointments/', {
        params: {
          status: 'confirmed',
          upcoming: true,
          limit,
        },
      });
      return response.data.results || response.data;
    } catch (error) {
      console.error('Failed to get upcoming appointments:', error);
      return [];
    }
  }

  /**
   * Get recent resumes
   */
  async getRecentResumes(limit: number = 5): Promise<any[]> {
    try {
      const response = await apiClient.get('/resumes/', {
        params: { limit, ordering: '-created_at' },
      });
      return response.data.results || response.data;
    } catch (error) {
      console.error('Failed to get recent resumes:', error);
      return [];
    }
  }
}

const dashboardService = new DashboardService();
export default dashboardService;
