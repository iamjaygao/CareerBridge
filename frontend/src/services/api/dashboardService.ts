import apiClient from './client';

export interface DashboardStats {
  upcomingAppointments: number;
  resumesUploaded: number;
  mentorSessions: number;
  profileViews: number;
}

export interface RecentActivity {
  id: string;
  type: string;
  description: string;
  timestamp: string;
}

export interface DashboardData {
  stats: DashboardStats;
  activities: RecentActivity[];
}

const dashboardService = {
  async getDashboardData(): Promise<DashboardData> {
    const response = await apiClient.get<DashboardData>('/users/dashboard/stats/');
    return response.data;
  },

  async getRecentActivities(): Promise<RecentActivity[]> {
    // For now, return activities from the main dashboard data
    const response = await apiClient.get<DashboardData>('/users/dashboard/stats/');
    return response.data.activities;
  },
};

export default dashboardService;