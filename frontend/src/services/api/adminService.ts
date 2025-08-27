import apiClient from './client';

export interface DashboardStats {
  total_users: number;
  active_users_today: number;
  new_users_today: number;
  total_mentors: number;
  active_mentors: number;
  pending_applications: number;
  total_appointments: number;
  appointments_today: number;
  completed_today: number;
  total_revenue: number;
  revenue_today: number;
  avg_response_time: number;
  error_rate: number;
  uptime_percentage: number;
}

export interface SystemStats {
  id: number;
  metric_name: string;
  metric_value: number;
  metric_unit: string;
  timestamp: string;
  category: string;
}

export interface AdminAction {
  id: number;
  admin_user: {
    id: number;
    username: string;
    email: string;
  };
  action_type: string;
  action_data: any;
  target_model: string;
  target_id: number;
  ip_address: string;
  user_agent: string;
  created_at: string;
}

export interface SystemConfig {
  id: number;
  config_key: string;
  config_value: string;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DataExport {
  id: number;
  export_type: string;
  file_path: string;
  file_size: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_by: {
    id: number;
    username: string;
  };
  created_at: string;
  completed_at?: string;
}

export interface ContentModeration {
  id: number;
  content_type: string;
  content_id: number;
  reported_by: {
    id: number;
    username: string;
  };
  reason: string;
  status: 'pending' | 'reviewed' | 'resolved' | 'dismissed';
  admin_notes?: string;
  action_taken?: string;
  created_at: string;
  updated_at: string;
}

export interface UserManagementData {
  users: Array<{
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    is_active: boolean;
    date_joined: string;
    last_login: string;
    role: string;
  }>;
  total_count: number;
  active_count: number;
  inactive_count: number;
}

export interface MentorManagementData {
  mentors: Array<{
    id: number;
    user: {
      id: number;
      username: string;
      email: string;
      first_name: string;
      last_name: string;
    };
    current_position: string;
    status: string;
    hourly_rate: number;
    total_sessions: number;
    average_rating: number;
    created_at: string;
  }>;
  total_count: number;
  active_count: number;
  pending_count: number;
}

export interface SystemHealth {
  database_status: 'healthy' | 'warning' | 'error';
  cache_status: 'healthy' | 'warning' | 'error';
  external_services: Array<{
    name: string;
    status: 'healthy' | 'warning' | 'error';
    response_time: number;
    last_check: string;
  }>;
  system_metrics: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    active_connections: number;
  };
  last_updated: string;
}

const adminService = {
  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await apiClient.get<DashboardStats>('/adminpanel/dashboard/');
    return response.data;
  },

  // System Stats
  async getSystemStats(): Promise<SystemStats[]> {
    const response = await apiClient.get<SystemStats[]>('/adminpanel/stats/');
    return response.data;
  },

  async getSystemStatsById(id: number): Promise<SystemStats> {
    const response = await apiClient.get<SystemStats>(`/adminpanel/stats/${id}/`);
    return response.data;
  },

  // Admin Actions
  async getAdminActions(): Promise<AdminAction[]> {
    const response = await apiClient.get<AdminAction[]>('/adminpanel/actions/');
    return response.data;
  },

  // System Config
  async getSystemConfigs(): Promise<SystemConfig[]> {
    const response = await apiClient.get<SystemConfig[]>('/adminpanel/config/');
    return response.data;
  },

  async getSystemConfigById(id: number): Promise<SystemConfig> {
    const response = await apiClient.get<SystemConfig>(`/adminpanel/config/${id}/`);
    return response.data;
  },

  async updateSystemConfig(id: number, data: Partial<SystemConfig>): Promise<SystemConfig> {
    const response = await apiClient.patch<SystemConfig>(`/adminpanel/config/${id}/`, data);
    return response.data;
  },

  // Data Export
  async getDataExports(): Promise<DataExport[]> {
    const response = await apiClient.get<DataExport[]>('/adminpanel/exports/');
    return response.data;
  },

  async createDataExport(data: { export_type: string }): Promise<DataExport> {
    const response = await apiClient.post<DataExport>('/adminpanel/exports/', data);
    return response.data;
  },

  async getDataExportById(id: number): Promise<DataExport> {
    const response = await apiClient.get<DataExport>(`/adminpanel/exports/${id}/`);
    return response.data;
  },

  // Content Moderation
  async getContentModeration(): Promise<ContentModeration[]> {
    const response = await apiClient.get<ContentModeration[]>('/adminpanel/moderation/');
    return response.data;
  },

  async updateContentModeration(id: number, data: Partial<ContentModeration>): Promise<ContentModeration> {
    const response = await apiClient.patch<ContentModeration>(`/adminpanel/moderation/${id}/`, data);
    return response.data;
  },

  // User Management
  async getUsers(): Promise<any[]> {
    const response = await apiClient.get<any[]>('/adminpanel/users/');
    return response.data;
  },

  async createUser(userData: {
    username: string;
    email: string;
    password: string;
    role?: string;
  }): Promise<any> {
    const response = await apiClient.post('/adminpanel/users/', {
      action: 'create',
      ...userData
    });
    return response.data;
  },

  async updateUser(userId: number, userData: {
    username?: string;
    email?: string;
    role?: string;
    is_staff?: boolean;
  }): Promise<any> {
    const response = await apiClient.post('/adminpanel/users/', {
      action: 'update',
      user_id: userId,
      ...userData
    });
    return response.data;
  },

  async deleteUser(userId: number): Promise<any> {
    const response = await apiClient.post('/adminpanel/users/', {
      action: 'delete',
      user_id: userId
    });
    return response.data;
  },

  async updateUserStatus(userId: number, action: string): Promise<any> {
    const response = await apiClient.post('/adminpanel/users/', {
      user_id: userId,
      action: action
    });
    return response.data;
  },

  // Mentor Management
  async getMentors(): Promise<any[]> {
    const response = await apiClient.get<any[]>('/adminpanel/mentors/');
    return response.data;
  },

  async updateMentorStatus(mentorId: number, action: string): Promise<any> {
    const response = await apiClient.post('/adminpanel/mentors/', {
      mentor_id: mentorId,
      action: action
    });
    return response.data;
  },

  // Mentor Applications
  async getMentorApplications(params?: {
    status?: string;
    search?: string;
  }): Promise<any[]> {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.search) queryParams.append('search', params.search);
    
    const url = `/adminpanel/mentors/applications/${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    const response = await apiClient.get<any[]>(url);
    return response.data;
  },

  async approveMentorApplication(applicationId: number): Promise<any> {
    const response = await apiClient.post('/adminpanel/mentors/applications/', {
      action: 'approve',
      application_id: applicationId
    });
    return response.data;
  },

  async rejectMentorApplication(applicationId: number, rejectionReason: string): Promise<any> {
    const response = await apiClient.post('/adminpanel/mentors/applications/', {
      action: 'reject',
      application_id: applicationId,
      rejection_reason: rejectionReason
    });
    return response.data;
  },

  // System Health
  async getSystemHealth(): Promise<SystemHealth> {
    const response = await apiClient.get<SystemHealth>('/adminpanel/health/');
    return response.data;
  },
};

export default adminService; 