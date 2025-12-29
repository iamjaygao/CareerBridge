import { DashboardStats, SystemHealth } from '../../types';
// Use the shared api client so baseURL and auth headers stay consistent
import apiClient from './client';

class AdminService {
  /**
   * Get dashboard statistics - aggregated metrics only
   */
  async getDashboardStats(): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/dashboard-stats/');
      return response.data;
    } catch (error) {
      console.error('Failed to get dashboard stats:', error);
      throw error;
    }
  }

  /**
   * Get staff dashboard statistics (legacy endpoint with staff access)
   */
  async getStaffDashboardStats(): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/dashboard/');
      return response.data;
    } catch (error) {
      console.error('Failed to get staff dashboard stats:', error);
      throw error;
    }
  }

  /**
   * Get all users
   */
  async getUsers(params?: any): Promise<any> {
    try {
      console.log('>>> DEBUG: adminService.getUsers called with params:', params);
      const response = await apiClient.get('/adminpanel/users/', { params });
      console.log('>>> DEBUG: adminService.getUsers raw response:', response);
      console.log('>>> DEBUG: adminService.getUsers response.data:', response.data);
      console.log('>>> DEBUG: adminService.getUsers response.data type:', typeof response.data);
      console.log('>>> DEBUG: adminService.getUsers response.data isArray:', Array.isArray(response.data));
      return response.data;
    } catch (error: any) {
      console.error('>>> DEBUG: adminService.getUsers ERROR:', error);
      console.error('>>> DEBUG: adminService.getUsers error.response:', error?.response);
      console.error('>>> DEBUG: adminService.getUsers error.response.data:', error?.response?.data);
      throw error;
    }
  }

  /**
   * Search users for support workflows
   */
  async searchUsers(params?: { search?: string; limit?: number }): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/users/search/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to search users:', error);
      throw error;
    }
  }

  /**
   * Update user
   */
  async updateUser(userId: number, data: any): Promise<any> {
    try {
      // Backend expects user_id and action in the request body for POST request
      const response = await apiClient.post('/adminpanel/users/', {
        action: 'update',
        user_id: userId,
        ...data
      });
      return response.data;
    } catch (error) {
      console.error('Failed to update user:', error);
      throw error;
    }
  }

  /**
   * Delete user
   */
  async deleteUser(userId: number): Promise<void> {
    try {
      await apiClient.delete(`/adminpanel/users/${userId}/`);
    } catch (error) {
      console.error('Failed to delete user:', error);
      throw error;
    }
  }

  /**
   * Get mentor applications
   */
  async getMentorApplications(params?: any): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/mentors/applications/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get mentor applications:', error);
      throw error;
    }
  }

  /**
   * Approve mentor application
   */
  async approveMentorApplication(applicationId: number): Promise<any> {
    try {
      const response = await apiClient.post(`/adminpanel/mentors/applications/${applicationId}/approve/`);
      return response.data;
    } catch (error) {
      console.error('Failed to approve mentor application:', error);
      throw error;
    }
  }

  /**
   * Reject mentor application
   */
  async rejectMentorApplication(applicationId: number, reason?: string): Promise<any> {
    try {
      const response = await apiClient.post(`/adminpanel/mentors/applications/${applicationId}/reject/`, {
        reason,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to reject mentor application:', error);
      throw error;
    }
  }

  /**
   * Get all appointments
   */
  async getAppointments(params?: any): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/appointments/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get appointments:', error);
      throw error;
    }
  }

  /**
   * Get staff appointments
   */
  async getStaffAppointments(params?: any): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/staff/appointments/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get staff appointments:', error);
      throw error;
    }
  }

  /**
   * Update appointment
   */
  async updateAppointment(appointmentId: number, data: any): Promise<any> {
    try {
      const response = await apiClient.put(`/adminpanel/appointments/${appointmentId}/`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to update appointment:', error);
      throw error;
    }
  }

  /**
   * Update staff appointment
   */
  async updateStaffAppointment(appointmentId: number, data: any): Promise<any> {
    try {
      const response = await apiClient.put(`/adminpanel/staff/appointments/${appointmentId}/`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to update staff appointment:', error);
      throw error;
    }
  }

  /**
   * Get system health
   */
  async getSystemHealth(): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/health/');
      return response.data;
    } catch (error) {
      console.error('Failed to get system health:', error);
      throw error;
    }
  }

  /**
   * Create user
   */
  async createUser(data: any): Promise<any> {
    try {
      // Backend expects action='create' in the request body
      const response = await apiClient.post('/adminpanel/users/', {
        action: 'create',
        ...data
      });
      return response.data;
    } catch (error) {
      console.error('Failed to create user:', error);
      throw error;
    }
  }

  /**
   * Update user status
   */
  async updateUserStatus(userId: number, action: string): Promise<any> {
    try {
      // Backend expects POST to /adminpanel/users/ with action and user_id
      const response = await apiClient.post('/adminpanel/users/', {
        action: action, // 'activate', 'deactivate'
        user_id: userId
      });
      return response.data;
    } catch (error) {
      console.error('Failed to update user status:', error);
      throw error;
    }
  }

  /**
   * Get payment statistics
   */
  async getPaymentStatistics(): Promise<any> {
    try {
      console.log('>>> DEBUG: adminService.getPaymentStatistics called');
      const response = await apiClient.get('/payments/statistics/');
      console.log('>>> DEBUG: adminService.getPaymentStatistics raw response:', response);
      console.log('>>> DEBUG: adminService.getPaymentStatistics response.data:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('>>> DEBUG: adminService.getPaymentStatistics ERROR:', error);
      console.error('>>> DEBUG: Error response:', error?.response);
      console.error('>>> DEBUG: Error response data:', error?.response?.data);
      throw error;
    }
  }

  /**
   * Get job statistics and crawler logs
   * TODO: Backend endpoint /adminpanel/jobs/stats/ should return:
   * { total_jobs: number, active_crawlers: number, last_crawl: string, crawler_logs: Array<{id, timestamp, status, jobs_found}> }
   */
  async getJobStats(): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/jobs/stats/');
      return response.data;
    } catch (error) {
      console.error('Failed to get job stats:', error);
      throw error;
    }
  }

  /**
   * Trigger job crawler (SuperAdmin only)
   * TODO: Backend endpoint POST /adminpanel/jobs/crawler/trigger/
   */
  async triggerCrawler(): Promise<any> {
    try {
      const response = await apiClient.post('/adminpanel/jobs/crawler/trigger/');
      return response.data;
    } catch (error) {
      console.error('Failed to trigger crawler:', error);
      throw error;
    }
  }

  /**
   * Clean expired jobs (SuperAdmin only)
   * TODO: Backend endpoint POST /adminpanel/jobs/clean-expired/
   */
  async cleanExpiredJobs(): Promise<any> {
    try {
      const response = await apiClient.post('/adminpanel/jobs/clean-expired/');
      return response.data;
    } catch (error) {
      console.error('Failed to clean expired jobs:', error);
      throw error;
    }
  }

  /**
   * Get assessment statistics
   * TODO: Backend endpoint /adminpanel/assessments/stats/ should return:
   * { total_assessments: number, total_resumes: number, ai_usage: number }
   */
  async getAssessmentStats(): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/assessments/stats/');
      return response.data;
    } catch (error) {
      console.error('Failed to get assessment stats:', error);
      throw error;
    }
  }

  /**
   * Get assessments list
   * TODO: Backend endpoint /adminpanel/assessments/ should return array of assessment objects
   */
  async getAssessments(params?: any): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/assessments/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get assessments:', error);
      throw error;
    }
  }

  /**
   * Get payouts list
   * TODO: Backend endpoint /adminpanel/payouts/ should return array of payout objects
   */
  async getPayouts(params?: any): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/payouts/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get payouts:', error);
      throw error;
    }
  }

  /**
   * Approve payout
   * TODO: Backend endpoint POST /adminpanel/payouts/{id}/approve/
   */
  async approvePayout(payoutId: number, notes?: string): Promise<any> {
    try {
      const response = await apiClient.post(`/adminpanel/payouts/${payoutId}/approve/`, { notes });
      return response.data;
    } catch (error) {
      console.error('Failed to approve payout:', error);
      throw error;
    }
  }

  /**
   * Reject payout
   * TODO: Backend endpoint POST /adminpanel/payouts/{id}/reject/
   */
  async rejectPayout(payoutId: number, notes?: string): Promise<any> {
    try {
      const response = await apiClient.post(`/adminpanel/payouts/${payoutId}/reject/`, { notes });
      return response.data;
    } catch (error) {
      console.error('Failed to reject payout:', error);
      throw error;
    }
  }

  /**
   * Get content items
   * TODO: Backend endpoint /adminpanel/content/ should return array of content objects
   */
  async getContent(params?: any): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/content/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get content:', error);
      throw error;
    }
  }

  /**
   * Get support tickets
   */
  async getSupportTickets(params?: any): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/support/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get support tickets:', error);
      throw error;
    }
  }

  /**
   * Update support ticket
   */
  async updateSupportTicket(ticketId: number, data: any): Promise<any> {
    try {
      const response = await apiClient.patch(`/adminpanel/support/${ticketId}/`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to update support ticket:', error);
      throw error;
    }
  }

  /**
   * Create support ticket
   */
  async createSupportTicket(data: any): Promise<any> {
    try {
      const response = await apiClient.post('/adminpanel/support/', data);
      return response.data;
    } catch (error) {
      console.error('Failed to create support ticket:', error);
      throw error;
    }
  }

  /**
   * Create content item
   * TODO: Backend endpoint POST /adminpanel/content/
   */
  async createContent(data: any): Promise<any> {
    try {
      const response = await apiClient.post('/adminpanel/content/', data);
      return response.data;
    } catch (error) {
      console.error('Failed to create content:', error);
      throw error;
    }
  }

  /**
   * Update content item
   * TODO: Backend endpoint PUT /adminpanel/content/{id}/
   */
  async updateContent(contentId: number, data: any): Promise<any> {
    try {
      const response = await apiClient.put(`/adminpanel/content/${contentId}/`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to update content:', error);
      throw error;
    }
  }

  /**
   * Delete content item
   * TODO: Backend endpoint DELETE /adminpanel/content/{id}/
   */
  async deleteContent(contentId: number): Promise<void> {
    try {
      await apiClient.delete(`/adminpanel/content/${contentId}/`);
    } catch (error) {
      console.error('Failed to delete content:', error);
      throw error;
    }
  }

  /**
   * Get promotions
   * TODO: Backend endpoint /adminpanel/promotions/ should return array of promotion objects
   */
  async getPromotions(params?: any): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/promotions/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get promotions:', error);
      throw error;
    }
  }

  /**
   * Create promotion
   * TODO: Backend endpoint POST /adminpanel/promotions/
   */
  async createPromotion(data: any): Promise<any> {
    try {
      const response = await apiClient.post('/adminpanel/promotions/', data);
      return response.data;
    } catch (error) {
      console.error('Failed to create promotion:', error);
      throw error;
    }
  }

  /**
   * Update promotion
   * TODO: Backend endpoint PUT /adminpanel/promotions/{id}/
   */
  async updatePromotion(promotionId: number, data: any): Promise<any> {
    try {
      const response = await apiClient.put(`/adminpanel/promotions/${promotionId}/`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to update promotion:', error);
      throw error;
    }
  }

  /**
   * Delete promotion
   * TODO: Backend endpoint DELETE /adminpanel/promotions/{id}/
   */
  async deletePromotion(promotionId: number): Promise<void> {
    try {
      await apiClient.delete(`/adminpanel/promotions/${promotionId}/`);
    } catch (error) {
      console.error('Failed to delete promotion:', error);
      throw error;
    }
  }

  /**
   * Get all mentors (for SuperAdmin)
   * Uses existing mentor management endpoint
   */
  async getAllMentors(params?: any): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/mentors/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get all mentors:', error);
      throw error;
    }
  }

  /**
   * Get system configuration
   * TODO: Backend endpoint /adminpanel/system/config/ should return system config object
   */
  async getSystemConfig(): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/system/config/');
      return response.data;
    } catch (error) {
      console.error('Failed to get system config:', error);
      throw error;
    }
  }

  /**
   * Update system configuration
   * TODO: Backend endpoint PUT /adminpanel/system/config/
   */
  async updateSystemConfig(config: any): Promise<any> {
    try {
      const response = await apiClient.put('/adminpanel/system/config/', config);
      return response.data;
    } catch (error) {
      console.error('Failed to update system config:', error);
      throw error;
    }
  }

  /**
   * Clear cache
   */
  async clearCache(): Promise<any> {
    try {
      const response = await apiClient.post('/adminpanel/system/actions/clear-cache/');
      return response.data;
    } catch (error) {
      console.error('Failed to clear cache:', error);
      throw error;
    }
  }

  /**
   * Get system settings
   */
  async getSystemSettings(): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/system/settings/');
      return response.data;
    } catch (error) {
      console.error('Failed to get system settings:', error);
      throw error;
    }
  }

  /**
   * Update system settings
   */
  async updateSystemSettings(data: any): Promise<any> {
    try {
      const response = await apiClient.put('/adminpanel/system/settings/', data);
      return response.data;
    } catch (error) {
      console.error('Failed to update system settings:', error);
      throw error;
    }
  }

  /**
   * Get error logs
   */
  async getErrorLogs(): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/system/actions/error-logs/');
      return response.data;
    } catch (error) {
      console.error('Failed to get error logs:', error);
      throw error;
    }
  }

  /**
   * Get admin action logs
   */
  async getAdminActions(params?: any): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/actions/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get admin actions:', error);
      throw error;
    }
  }

  /**
   * Create a data export request
   */
  async createDataExport(payload: any): Promise<any> {
    try {
      const response = await apiClient.post('/adminpanel/exports/', payload);
      return response.data;
    } catch (error) {
      console.error('Failed to create data export:', error);
      throw error;
    }
  }

  /**
   * Get data export requests
   */
  async getDataExports(params?: any): Promise<any> {
    try {
      const response = await apiClient.get('/adminpanel/exports/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get data exports:', error);
      throw error;
    }
  }

  /**
   * Reset rate limits
   */
  async resetRateLimits(): Promise<any> {
    try {
      const response = await apiClient.post('/adminpanel/system/actions/reset-rate-limits/');
      return response.data;
    } catch (error) {
      console.error('Failed to reset rate limits:', error);
      throw error;
    }
  }

  /**
   * Rebuild search index
   */
  async rebuildSearchIndex(): Promise<any> {
    try {
      const response = await apiClient.post('/adminpanel/system/actions/rebuild-index/');
      return response.data;
    } catch (error) {
      console.error('Failed to rebuild search index:', error);
      throw error;
    }
  }
}

// AdminDashboardStats is now just an alias/extension of DashboardStats from types
export type AdminDashboardStats = DashboardStats;

// AdminSystemHealth is now just an alias/extension of SystemHealth from types
export type AdminSystemHealth = SystemHealth;

const adminService = new AdminService();
export default adminService;
