// User related types
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  avatar?: string;
  role: 'user' | 'mentor' | 'admin';
  is_verified: boolean;
  created_at: string;
  last_login: string;
  // Optional profile fields (may not be implemented in backend yet)
  phone?: string;
  location?: string;
  bio?: string;
  linkedin_url?: string;
  github_url?: string;
}

export interface LoginRequest {
  login: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
}

export interface PasswordChangeRequest {
  old_password: string;
  new_password: string;
  new_password_confirm: string;
}

// Common types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
}

// Theme and styling types
export interface ThemeConfig {
  mode: 'light' | 'dark';
  primaryColor: string;
  secondaryColor: string;
}

// Route types
export interface RouteConfig {
  path: string;
  element: React.ComponentType;
  layout?: React.ComponentType;
  roles?: string[];
  children?: RouteConfig[];
}

// Form types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'select' | 'date' | 'file' | 'textarea';
  required?: boolean;
  options?: { label: string; value: string | number }[];
  validation?: {
    required?: string;
    pattern?: {
      value: RegExp;
      message: string;
    };
    minLength?: {
      value: number;
      message: string;
    };
    maxLength?: {
      value: number;
      message: string;
    };
  };
}

// Redux related types
export interface ReduxAction<T = any> {
  type: string;
  payload?: T;
  error?: boolean;
  meta?: any;
}

export interface ReduxState {
  loading: boolean;
  error: string | null;
  data: any;
}

// API Error types
export interface ApiError {
  status: number;
  code: string;
  message: string;
  details?: Record<string, string[]>;
}

// Notification types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  title?: string;
  duration?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

// File upload types
export interface FileUploadResponse {
  url: string;
  filename: string;
  size: number;
  mime_type: string;
}

export interface FileUploadProgress {
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
}

// Appointment types
export interface Appointment {
  id: number;
  user: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    avatar?: string;
  };
  mentor: {
    id: number;
    user: {
      id: number;
      username: string;
      email: string;
      first_name: string;
      last_name: string;
      avatar?: string;
    };
    current_position?: string;
    bio?: string;
    hourly_rate?: number;
  };
  time_slot: {
    id: number;
    start_time: string;
    end_time: string;
    price: number;
    currency: string;
  };
  title: string;
  description: string;
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'no_show';
  scheduled_start: string;
  scheduled_end: string;
  actual_start?: string;
  actual_end?: string;
  price: number;
  currency: string;
  is_paid: boolean;
  payment_method?: string;
  meeting_link?: string;
  meeting_platform?: string;
  meeting_notes?: string;
  user_rating?: number;
  user_feedback?: string;
  mentor_rating?: number;
  mentor_feedback?: string;
  cancellation_reason?: string;
  cancelled_by?: string;
  cancellation_fee?: number;
  refund_amount?: number;
  created_at: string;
  updated_at: string;
}

// Date and time types
export interface DateRange {
  start: Date;
  end: Date;
}

export interface TimeSlot {
  start: string;
  end: string;
  available: boolean;
}

// Search and filter types
export interface SearchFilters {
  query?: string;
  sort?: string;
  order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
  [key: string]: any;
}

// Chart and analytics types
export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
  }[];
}

export interface AnalyticsMetric {
  label: string;
  value: number;
  unit?: string;
  change?: number;
  trend?: 'up' | 'down' | 'stable';
}

export interface BreadcrumbItem {
  label: string;
  path: string;
}

export interface MentorDetail {
  id: number;
  user: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    avatar?: string;
  };
  bio: string;
  years_of_experience: number;
  current_position: string;
  industry: string;
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
  services: MentorService[];
  reviews: MentorReview[];
  availability: MentorAvailability[];
}

export interface MentorService {
  id: number;
  service_type: string;
  title: string;
  description: string;
  pricing_model: string;
  price_per_hour?: number;
  fixed_price?: number;
  package_price?: number;
  package_sessions?: number;
  duration_minutes: number;
  display_price: string;
  is_active: boolean;
}

export interface MentorReview {
  id: number;
  rating: number;
  comment: string;
  created_at: string;
  user: {
    username: string;
    avatar?: string;
  };
}

export interface MentorAvailability {
  id: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  is_active: boolean;
}

export interface Mentor {
  id: number;
  user: User;
  first_name?: string;
  last_name?: string;
  avatar?: string;
  title?: string;
  company?: string;
  bio: string;
  industry: string;
  current_position: string;
  years_of_experience: number;
  experience_years?: number;
  status: string;
  average_rating: number;
  total_reviews: number;
  review_count?: number;
  total_sessions: number;
  total_earnings: number;
  hourly_rate?: number;
  rating?: number;
  is_verified: boolean;
  verification_badge: string;
  specializations: string[];
  skills?: string[];
  ranking_score: number;
  is_approved: boolean;
  location?: string;
  education?: string;
  availability_status?: string;
  created_at: string;
  updated_at: string;
}

export interface MentorFilters {
  service_type?: string;
  industry?: string;
  min_rating?: number;
  is_verified?: boolean;
  search?: string;
}