// User Types

export type UserRole ='admin' | 'mentor' | 'student' | 'staff'| 'superadmin';

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  avatar?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  location?: string;
  bio?: string;
  linkedin_url?: string;
  github_url?: string;
  is_verified?: boolean;
  email_verified?: boolean;
  created_at?: string;
  last_login?: string;
  date_joined?: string;
  // Django authentication flags
  is_superuser?: boolean;
  is_staff?: boolean;
  is_authenticated?: boolean;
}

// Mentor Types
export interface Mentor {
  id: number;

  // ======================
  // User
  // ======================
  user: User;

  // ======================
  // Core profile (MentorProfileSerializer)
  // ======================
  bio: string;
  headline: string;              // SerializerMethodField
  job_title: string;             // source=current_position
  industry?: string;

  // ======================
  // Expertise & focus
  // ======================
  expertise: string[];            // source=specializations
  primary_focus?: string;
  session_focus?: string;
  mentor_card?: {
    line1: string;
    line2: string;
  };

  // ======================
  // Pricing
  // ======================
  starting_price: number;         // computed
  hourly_rate?: number;           // optional fallback

  // ======================
  // Ratings & stats
  // ======================
  rating: number | null;                 // average_rating
  review_count: number;           // total_reviews
  total_sessions?: number;

  // ======================
  // Verification & status
  // ======================
  is_verified: boolean;
  status?: 'pending' | 'approved' | 'rejected';
  badges?: string[];
  price_label: string;          // e.g. "From $120"
  price_unit: 'session';        // future-proof
  trust_label?: string | null;  // shown when rating === null
  cta_action?: 'view' | 'unlock' | 'book';
  display_name?: string;
  hero_title?: string;
  hero_headline?: string;
  hero_subline?: string;

  // ======================
  // 🔥 SaaS Positioning Core（新增）
  // ======================
  primary_track?: 
    | 'resume_review'
    | 'mock_interview'
    | 'career_switch'
    | 'advanced_interview';

  system_role?: string;           // e.g. "Senior System Design Reviewer"
  system_insight?: string;        // e.g. "Frequently booked mentor"
  cta_label?: string;             // e.g. "Prepare for interviews"
  ranking_reason?: string;
  primary_service_id?: number;    // ID of the mentor's primary service

  // ======================
  // Optional / UI-safe
  // ======================
  location?: string;
  services?: MentorService[];     // Available for MentorDetail, optional for Mentor list items
}

export interface MentorService {
  id: number;
  service_type: 'resume_review' | 'mock_interview' | 'career_consultation';
  title: string;
  description: string;
  pricing_model: 'hourly' | 'fixed' | 'package';
  price_per_hour?: number;
  fixed_price?: number;
  package_price?: number;
  duration_minutes: number;
  display_price?: string;
  is_active?: boolean;
}

export interface MentorDetail extends Mentor {
  services: MentorService[];
  availability?: any[];
  reviews?: any[];
}

// Appointment Types
export interface Appointment {
  id: number;
  mentor: number | Mentor;
  user: number | User;
  date: string;
  time: string;
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled' | string;
  is_paid?: boolean;
  notes?: string;
  meeting_link?: string;
  meeting_platform?: string;
  user_feedback?: any;
  mentor_feedback?: any;
  user_rating?: number;
  scheduled_start?: string;
  scheduled_end?: string;
  title?: string;
  created_at?: string;
  updated_at?: string;
}

// Resume Types
export interface Resume {
  id: number;
  title: string;
  file: string;
  status: 'uploaded' | 'analyzing' | 'analyzed' | 'failed';
  created_at: string;
  analyzed_at?: string;
  uploaded_at?: string; // Alias for created_at
  file_type?: string;
  file_size?: number;
  analysis?: ResumeAnalysis;
  analysis_result?: ResumeAnalysis; // Alias for analysis
}

export interface ResumeAnalysis {
  overall_score: number;
  structure_score: number;
  content_score: number;
  keyword_score: number;
  ats_score: number;
  technical_skills: string[];
  soft_skills: string[];
  skill_gaps: string[];
  feedback?: ResumeFeedback;
}

export interface ResumeFeedback {
  summary: string;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

// Breadcrumb Types
export interface BreadcrumbItem {
  label: string;
  path: string;
}

// API Response Types
export interface ApiResponse<T> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

// Pagination Types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Search Types
export interface SearchFilters {
  query?: string;
  location?: string;
  industry?: string;
  skills?: string[];
  minRating?: number;
  maxPrice?: number;
}

// Notification Types
export interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
}

// Form Types
export interface FormField {
  name: string;
  label: string;
  type: string;
  required?: boolean;
  options?: Array<{ value: any; label: string }>;
  disabled?: boolean;
}

// Chat Types
export interface ChatMessage {
  id: number;
  sender: number;
  content: string;
  timestamp: string;
  read: boolean;
}

export interface ChatRoom {
  id: number;
  participants: number[];
  lastMessage?: ChatMessage;
  last_message?: ChatMessage; // Alias
  unreadCount: number;
  unread_count?: number; // Alias
  mentor_name?: string;
  created_at?: string;
}

export interface ChatParticipant {
  id: number;
  username: string;
  avatar?: string;
}

// Filter Types
export interface MentorFilters {
  /* =====================
     Core (P0)
  ===================== */
  /**
   * What problem the user wants help with.
   * Drives both filtering and ranking.
   */
  primary_track?: 
    | 'resume_review'
    | 'mock_interview'
    | 'career_switch'
    | 'advanced_interview';

  /**
   * Ranking hint ONLY.
   * Must NOT be treated as a hard filter.
   */
  track?: 
    | 'resume_review'
    | 'mock_interview'
    | 'career_switch'
    | 'advanced_interview';

  /* =====================
     Secondary (P1)
  ===================== */
  /**
   * User's field / industry.
   */
  industry?: string;

  /* =====================
     Optional preferences
  ===================== */
  /**
   * Show only verified mentors.
   */
  is_verified?: boolean;

  /* =====================
     Search (low priority)
  ===================== */
  /**
   * Keyword search by background or expertise.
   */
  search?: string;

  /* =====================
     Pagination / misc
  ===================== */
  page?: number;
  limit?: number;
  experience_level?: string;
  specialization?: string;
}

export interface AppointmentFilters {
  status?: string;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  sort_by?: string;
}

// Dashboard Types
export interface TrendDataPoint {
  date: string;
  value: number;
}

export interface DashboardStats {
  // ==================== PLATFORM OVERVIEW ====================
  total_users?: number;
  total_students?: number;
  total_mentors?: number;
  total_admins?: number;
  total_staff?: number;
  
  // ==================== MONTHLY METRICS WITH MoM/YoY ====================
  new_users_this_month?: number;
  user_mom?: number | null;
  user_yoy?: number | null;
  
  new_students_this_month?: number;
  student_mom?: number | null;
  student_yoy?: number | null;
  
  new_mentors_this_month?: number;
  mentor_mom?: number | null;
  mentor_yoy?: number | null;
  
  new_staff_this_month?: number;
  staff_mom?: number | null;
  staff_yoy?: number | null;
  
  // ==================== APPOINTMENT METRICS ====================
  appointments_this_month?: number;
  appointments_last_month_same_period?: number;
  appointment_mom?: number | null;
  appointment_yoy?: number | null;
  cancellation_rate?: number;
  
  // ==================== RESUME METRICS ====================
  resumes_uploaded_this_month?: number;
  resume_mom?: number | null;
  resume_yoy?: number | null;
  
  // ==================== TREND DATASETS (7-DAY) ====================
  users_7_day?: TrendDataPoint[];
  mentors_7_day?: TrendDataPoint[];
  appointments_7_day?: TrendDataPoint[];
  resumes_7_day?: TrendDataPoint[];
  
  // ==================== OPERATIONAL METRICS ====================
  active_mentors?: number;
  pending_mentor_approvals?: number;
  pending_resume_reviews?: number;
  active_admins_today?: number;
  active_staff_today?: number;
  
  // ==================== LEGACY FIELDS (for backward compatibility) ====================
  students?: number;
  active_users_today?: number;
  new_users_today?: number;
  pending_applications?: number;
  appointments?: number;
  total_appointments?: number;
  appointments_today?: number;
  completed_today?: number;
  assessments?: number;
  job_listings?: number;
  
  // System health and performance
  system_health?: string;
  avg_response_time?: number | null;  // Can be null if unavailable (unified with api_response_time)
  error_rate?: number;
  uptime_percentage?: number;
  
  // Financial statistics
  revenue_today?: number;
  total_revenue?: number;
  mentor_earnings?: number;
  platform_earnings?: number;
  pending_payouts?: number;
  revenue_trend?: Array<{ date: string; value: number }>;
  payment_success_rate?: number;
  payment_failure_rate?: number;
  refund_rate?: number;
  refund_amount_total?: number;
  net_revenue?: number;
  payout_pending_total?: number;
  payout_ready_total?: number;
  payout_paid_total?: number;
  payout_failed_total?: number;
  payout_on_hold_total?: number;
  payout_exposure_total?: number;
  
  // Additional legacy fields (for backward compatibility with other dashboards)
  upcomingAppointments?: number;
  resumesUploaded?: number;
  mentorSessions?: number;
  profileViews?: number;
  totalResumes?: number;
  completedSessions?: number;
  resumeAnalysisCount?: number;
  averageResumeScore?: number;
  active_connections?: number;
}

export interface RecentActivity {
  id: number;
  type: string;
  description: string;
  timestamp: string;
}

export interface SystemHealth {
  system_health: string;
  backend_status: string;
  database_status: string;
  cache_status: string;
  api_response_time: number | null;  // Can be null if unavailable
  error_rate: number;
  uptime_percentage: number;
  database?: string;
  cache?: string;
  status?: string;
  external_services?: Array<{
    name: string;
    status: string;
    response_time: number;
    last_check: string;
  }>;
  system_metrics?: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    active_connections: number;
  };
  last_updated?: string;
}

export interface SystemSettings {
  // Platform Settings
  platform_name: string;
  company_name: string;
  support_email: string;
  support_phone: string;
  office_address: string;
  website_url: string;
  
  // Contact Settings
  contact_title?: string;
  contact_description?: string;
  
  // Announcement Settings
  announcement_enabled: boolean;
  announcement_title?: string;
  announcement_text: string;
  announcement_message?: string; // Alias for announcement_text
  announcement_type: 'info' | 'warning' | 'error' | 'success';
  
  // Appearance Settings
  primary_color: string;
  accent_color?: string;
  secondary_color?: string; // Alias for accent_color
  logo_url: string;
  favicon_url: string;
  theme: 'light' | 'dark' | 'auto';
  enable_dark_mode?: boolean;
  
  // Contact & Social Links
  contact_email?: string;
  contact_phone?: string;
  linkedin_url: string;
  twitter_url: string;
  instagram_url: string;
  youtube_url: string;
  facebook_url?: string;
  
  // API Keys (masked in responses)
  openai_api_key?: string;
  stripe_secret_key?: string;
  stripe_api_key?: string; // Alias for stripe_secret_key
  email_api_key?: string;
  smtp_api_key?: string;
  google_oauth_key?: string;
  openai_api_key_masked?: string;
  stripe_secret_key_masked?: string;
  stripe_api_key_masked?: string;
  email_api_key_masked?: string;
  smtp_api_key_masked?: string;
  google_oauth_key_masked?: string;
  
  // Email Configuration
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password?: string;
  smtp_password_masked?: string;
  smtp_from_name: string;
  template_footer_text: string;
  enable_tls?: boolean;
  
  // Timestamps
  created_at?: string;
  updated_at?: string;
  updated_by?: number;
}
