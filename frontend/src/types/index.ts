// User types
export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'mentor' | 'student';
  avatar?: string;
  email_verified: boolean;
}

// Mentor types
export interface MentorProfile {
  id: number;
  user: User;
  bio: string;
  years_of_experience: number;
  current_position: string;
  industry: string;
  status: 'pending' | 'approved' | 'rejected';
  average_rating: number;
  total_reviews: number;
  total_sessions: number;
  total_earnings: number;
  is_verified: boolean;
  verification_badge?: string;
  specializations: string[];
  created_at: string;
  updated_at: string;
}

// Appointment types
export interface Appointment {
  id: number;
  user: User;
  mentor: MentorProfile;
  title: string;
  description?: string;
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'no_show';
  scheduled_start: string;
  scheduled_end: string;
  actual_start?: string;
  actual_end?: string;
  price: number;
  currency: string;
  is_paid: boolean;
  meeting_link?: string;
  meeting_platform?: string;
  user_rating?: number;
  user_feedback?: string;
  created_at: string;
  updated_at: string;
}

// Resume types
export interface Resume {
  id: number;
  user: User;
  title: string;
  file: string;
  status: 'uploaded' | 'analyzing' | 'analyzed' | 'failed';
  file_size: number;
  file_type: string;
  uploaded_at: string;
  analyzed_at?: string;
  created_at: string;
  updated_at: string;
}

// Payment types
export interface Payment {
  id: number;
  user: User;
  mentor?: MentorProfile;
  appointment?: Appointment;
  payment_type: 'appointment' | 'subscription' | 'refund';
  amount: number;
  currency: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled' | 'refunded';
  provider: 'stripe' | 'paypal';
  provider_payment_id?: string;
  platform_fee: number;
  mentor_earnings: number;
  created_at: string;
  updated_at: string;
}

// Notification types
export interface Notification {
  id: number;
  user: User;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  is_sent: boolean;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  related_appointment?: number;
  related_resume?: number;
  related_mentor?: number;
  sent_at?: string;
  read_at?: string;
  created_at: string;
}

// API Response types
export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

// Auth types
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
  role?: 'admin' | 'mentor' | 'student';
}

export interface PasswordChangeRequest {
  old_password: string;
  new_password: string;
  new_password_confirm: string;
}

// Form types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'textarea' | 'file';
  required?: boolean;
  options?: { value: string; label: string }[];
  validation?: any;
}

// UI types
export interface MenuItem {
  label: string;
  path: string;
  icon?: React.ReactNode;
  children?: MenuItem[];
}

export interface BreadcrumbItem {
  label: string;
  path?: string;
  active?: boolean;
} 