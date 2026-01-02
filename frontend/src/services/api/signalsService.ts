import apiClient from './client';
import { OS_API } from '../../os/apiPaths';

export interface ATSSignal {
  id: number;
  decision_slot_id: string;
  signal_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: string;
  message: string;
  details: Record<string, any>;
  section?: string;
  line_number?: number;
  engine_name: string;
  engine_version: string;
  signal_schema_version: string;
  is_critical: boolean;
  is_high_priority: boolean;
  created_at: string;
  updated_at: string;
}

export interface HumanReviewTask {
  id: number;
  signal: ATSSignal | null;
  decision_slot_id: string;
  task_type: string;
  status: 'pending' | 'assigned' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  assigned_to?: number;
  assigned_to_user?: {
    id: number;
    username: string;
    email: string;
    first_name?: string;
    last_name?: string;
  };
  assigned_at?: string;
  review_notes?: string;
  review_decision?: string;
  reviewed_at?: string;
  context_data: Record<string, any>;
  due_at?: string;
  is_critical: boolean;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
}

export interface SignalsDashboardData {
  decision_slot_id: string;
  signals: ATSSignal[];
  grouped_by_severity: {
    critical: ATSSignal[];
    high: ATSSignal[];
    medium: ATSSignal[];
    low: ATSSignal[];
    info: ATSSignal[];
  };
  total_count: number;
  critical_count: number;
  high_count: number;
}

export interface ReviewTasksData {
  decision_slot_id: string;
  review_tasks: HumanReviewTask[];
  total_count: number;
  pending_count: number;
  completed_count: number;
}

class SignalsService {
  /**
   * Get all ATS signals for a decision slot
   */
  async getSignalsByDecisionSlot(
    decisionSlotId: string,
    options?: {
      severity?: string;
      signalType?: string;
    }
  ): Promise<SignalsDashboardData> {
    try {
      const params = new URLSearchParams({ decision_slot_id: decisionSlotId });
      if (options?.severity) {
        params.append('severity', options.severity);
      }
      if (options?.signalType) {
        params.append('signal_type', options.signalType);
      }

      const response = await apiClient.get(`${OS_API.ATS_SIGNALS}?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch signals:', error);
      throw error;
    }
  }

  /**
   * Get a single ATS signal by ID
   */
  async getSignalById(signalId: number): Promise<ATSSignal> {
    try {
      const response = await apiClient.get(`${OS_API.ATS_SIGNALS}${signalId}/`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch signal:', error);
      throw error;
    }
  }

  /**
   * Get all review tasks for a decision slot
   */
  async getReviewTasksByDecisionSlot(
    decisionSlotId: string,
    options?: {
      status?: string;
      priority?: string;
    }
  ): Promise<ReviewTasksData> {
    try {
      const params = new URLSearchParams({ decision_slot_id: decisionSlotId });
      if (options?.status) {
        params.append('status', options.status);
      }
      if (options?.priority) {
        params.append('priority', options.priority);
      }

      const response = await apiClient.get(`${OS_API.HUMAN_LOOP}review-tasks/?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch review tasks:', error);
      throw error;
    }
  }

  /**
   * Get a single review task by ID
   */
  async getReviewTaskById(taskId: number): Promise<HumanReviewTask> {
    try {
      const response = await apiClient.get(`${OS_API.HUMAN_LOOP}review-tasks/${taskId}/`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch review task:', error);
      throw error;
    }
  }

  /**
   * Get complete dashboard data for a decision slot
   */
  async getDashboardData(decisionSlotId: string): Promise<{
    signals: SignalsDashboardData;
    reviewTasks: ReviewTasksData;
  }> {
    try {
      const [signals, reviewTasks] = await Promise.all([
        this.getSignalsByDecisionSlot(decisionSlotId),
        this.getReviewTasksByDecisionSlot(decisionSlotId),
      ]);

      return { signals, reviewTasks };
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      throw error;
    }
  }
}

const signalsService = new SignalsService();
export default signalsService;

