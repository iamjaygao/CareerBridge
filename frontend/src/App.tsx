import React, { Suspense, lazy, useEffect } from 'react';
import { Provider, useDispatch, useSelector } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  Outlet,
  useLocation,
  useParams,
} from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

// Redux Core
import { store, persistor, RootState } from './store';
import { initAuth } from './store/slices/authSlice';
import { setStoreRef } from './services/api/client';
import { preloadPopularData } from './services/api/searchService';

// Providers
import ErrorBoundary from './components/common/ErrorBoundary';
import LoadingSpinner from './components/common/LoadingSpinner';
import { NotificationProvider } from './components/common/NotificationProvider';
import { AuthProvider } from './contexts/AuthContext';
import { RoleProvider } from './contexts/RoleContext';
import { SystemSettingsProvider } from './contexts/SystemSettingsContext';
import theme from './theme/theme';

// Layouts
import PublicLayout from './components/layout/PublicLayout';
import StudentLayout from './components/layout/StudentLayout';
import MentorLayout from './components/layout/MentorLayout';
import StaffLayout from './components/layout/StaffLayout';
import AdminLayout from './components/layout/AdminLayout';
import SuperAdminLayout from './components/layout/SuperAdminLayout';

// Routes / Guards
import StudentRoute from './components/student/StudentRoute';
import MentorRoute from './components/mentor/MentorRoute';
import StaffRoute from './components/staff/StaffRoute';
import AdminRoute from './components/admin/AdminRoute';
import SuperAdminRoute from './components/superadmin/SuperAdminRoute';
import { getLandingPathByRole } from './utils/roleLanding';

/* ===========================
   Lazy Pages
=========================== */
// Public
const LandingPage = lazy(() => import('./pages/home/LandingPage'));
const LoginPage = lazy(() => import('./pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('./pages/auth/RegisterPage'));
const EmailVerificationPage = lazy(() => import('./pages/auth/EmailVerificationPage'));
const AboutPage = lazy(() => import('./pages/about/AboutPage'));
const ContactPage = lazy(() => import('./pages/contact/ContactPage'));
const BecomeMentorPage = lazy(() => import('./pages/become-mentor/BecomeMentorPage'));
const PublicAssessmentPage = lazy(() => import('./pages/assessment/AssessmentPage'));
const PublicIntelligencePage = lazy(() => import('./pages/intelligence/IntelligencePage'));
const PricingPage = lazy(() => import('./pages/pricing/PricingPage'));
const ResourcesPage = lazy(() => import('./pages/resources/ResourcesPage'));
const ResumeTipsPage = lazy(() => import('./pages/resources/ResumeTipsPage'));
const InterviewGuidePage = lazy(() => import('./pages/resources/InterviewGuidePage'));
const CareerRoadmapsPage = lazy(() => import('./pages/resources/CareerRoadmapsPage'));

// Student
const StudentDashboardPage = lazy(() => import('./pages/student/DashboardPage'));
const StudentAssessmentPage = lazy(() => import('./pages/student/AssessmentPage'));
const StudentInsightsPage = lazy(() => import('./pages/student/InsightsPage'));
const StudentIntelligencePage = lazy(() => import('./pages/student/IntelligencePage'));
const ResumeAnalysisDetailPage = lazy(() => import('./pages/student/ResumeAnalysisDetailPage'));
const StudentAppointmentsPage = lazy(() => import('./pages/student/AppointmentsPage'));
const StudentProfilePage = lazy(() => import('./pages/student/ProfilePage'));

// Mentors (shared)
const MentorListPage = lazy(() => import('./pages/mentors/MentorListPage'));
const MentorDetailPage = lazy(() => import('./pages/mentors/MentorDetailPage'));

// Mentor
const MentorDashboardPage = lazy(() => import('./pages/mentor/DashboardPage'));
const MentorProfilePage = lazy(() => import('./pages/mentor/ProfilePage'));
const MentorAvailabilityPage = lazy(() => import('./pages/mentor/AvailabilityPage'));
const MentorAppointmentsPage = lazy(() => import('./pages/mentor/AppointmentsPage'));
const MentorEarningsPage = lazy(() => import('./pages/mentor/EarningsPage'));
const MentorFeedbackPage = lazy(() => import('./pages/mentor/FeedbackPage'));
const MentorResourcesPage = lazy(() => import('./pages/mentor/ResourcesPage'));

// Staff
const StaffDashboardPage = lazy(() => import('./pages/staff/DashboardPage'));
const StaffMentorApprovalsPage = lazy(() => import('./pages/staff/mentors/MentorApprovalsPage'));
const StaffAppointmentsPage = lazy(() => import('./pages/staff/appointments/AppointmentsPage'));
const StaffResumesPage = lazy(() => import('./pages/staff/ResumesPage'));
const StaffContentManagementPage = lazy(() => import('./pages/staff/content/ContentManagementPage'));
const StaffUserSupportPage = lazy(() => import('./pages/staff/support/UserSupportPage'));
const StaffReportsPage = lazy(() => import('./pages/staff/reports/ReportsPage'));

// Admin
const AdminDashboardPage = lazy(() => import('./pages/admin/AdminDashboardPage'));
const AdminUserManagementPage = lazy(() => import('./pages/admin/UserManagementPage'));
const AdminMentorsPage = lazy(() => import('./pages/admin/mentors/MentorsPage'));
const AdminAppointmentsPage = lazy(() => import('./pages/admin/AppointmentManagementPage'));
const AdminAssessmentPage = lazy(() => import('./pages/admin/AssessmentPage'));
const AdminJobsPage = lazy(() => import('./pages/admin/JobsPage'));
const AdminExportsPage = lazy(() => import('./pages/admin/ExportsPage'));
const AdminContentPage = lazy(() => import('./pages/admin/content/ContentPage'));
const AdminPromotionsPage = lazy(() => import('./pages/admin/promotions/PromotionsPage'));
const AdminPayoutsPage = lazy(() => import('./pages/admin/payouts/PayoutsPage'));
const AnalyticsPage = lazy(() => import('./pages/analytics/AnalyticsPage'));

// SuperAdmin
const CommandCenter = lazy(() => import('./pages/superadmin/CommandCenter'));
const SuperAdminSystemSettingsPage = lazy(() => import('./pages/admin/system/SystemSettingsPage'));
const SuperAdminUsersPage = lazy(() => import('./pages/superadmin/UsersPage'));
const SuperAdminMentorsPage = lazy(() => import('./pages/superadmin/MentorsPage'));
const SuperAdminAppointmentsPage = lazy(() => import('./pages/superadmin/AppointmentsPage'));
const SuperAdminAssessmentPage = lazy(() => import('./pages/superadmin/AssessmentPage'));
const SuperAdminJobsPage = lazy(() => import('./pages/superadmin/JobsPage'));
const SuperAdminSystemPage = lazy(() => import('./pages/superadmin/SystemPage'));

// Notifications (shared)
const NotificationsPage = lazy(() => import('./pages/notifications/NotificationsPage'));

// Shared flows (authenticated)
const ProfilePage = lazy(() => import('./pages/profile/ProfilePage'));
const SettingsPage = lazy(() => import('./pages/settings/SettingsPage'));
const ChatListPage = lazy(() => import('./pages/chat/ChatListPage'));
const ChatRoomPage = lazy(() => import('./pages/chat/ChatRoomPage'));
const ResumeListPage = lazy(() => import('./pages/resumes/ResumeListPage'));
const UploadResumePage = lazy(() => import('./pages/resumes/UploadResumePage'));
const ResumeAnalysisPage = lazy(() => import('./pages/resumes/ResumeAnalysisPage'));

// Appointments (student)
const AppointmentDetailPage = lazy(() => import('./pages/appointments/AppointmentDetailPage'));
const CreateAppointmentPage = lazy(() => import('./pages/appointments/CreateAppointmentPage'));
const RescheduleAppointmentPage = lazy(() => import('./pages/appointments/RescheduleAppointmentPage'));

// Fallback
const NotFoundPage = lazy(() => import('./pages/error/NotFoundPage'));

/* ===========================
   Guards (In-file components)
=========================== */

const ProtectedGate: React.FC = () => {
  const { isAuthenticated, authLoaded } = useSelector(
    (state: RootState) => state.auth
  );

  if (!authLoaded) return <LoadingSpinner />;

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};

const DashboardRedirect: React.FC = () => {
  const role = useSelector((state: RootState) => state.auth.user?.role);
  if (!role) return <Navigate to="/login" replace />;
  return <Navigate to={getLandingPathByRole(role)} replace />;
};

const RoleRedirect: React.FC<{ targetByRole: Record<string, string> }> = ({ targetByRole }) => {
  const role = useSelector((state: RootState) => state.auth.user?.role);
  const location = useLocation();
  if (!role) return <Navigate to="/login" replace />;
  const target = targetByRole[role] || getLandingPathByRole(role);
  return <Navigate to={`${target}${location.search}`} replace />;
};

const AppointmentDetailRedirect: React.FC<{ action?: 'reschedule' }> = ({ action }) => {
  const role = useSelector((state: RootState) => state.auth.user?.role);
  const location = useLocation();
  const { id } = useParams();
  if (!role) return <Navigate to="/login" replace />;
  if (role === 'student' && id) {
    const suffix = action === 'reschedule' ? `/reschedule` : '';
    return (
      <Navigate to={`/student/appointments/${id}${suffix}${location.search}`} replace />
    );
  }
  return <Navigate to={getLandingPathByRole(role)} replace />;
};

const ResumeDetailRedirect: React.FC = () => {
  const role = useSelector((state: RootState) => state.auth.user?.role);
  const location = useLocation();
  const { id } = useParams();
  if (!role) return <Navigate to="/login" replace />;
  if (role === 'student' && id) {
    return <Navigate to={`/student/resumes/${id}/analysis${location.search}`} replace />;
  }
  return <Navigate to={getLandingPathByRole(role)} replace />;
};

const ChatRoomRedirect: React.FC = () => {
  const role = useSelector((state: RootState) => state.auth.user?.role);
  const location = useLocation();
  const { id } = useParams();
  if (!role) return <Navigate to="/login" replace />;
  if (id && (role === 'student' || role === 'mentor')) {
    const base = role === 'mentor' ? '/mentor/chat' : '/student/chat';
    return <Navigate to={`${base}/${id}${location.search}`} replace />;
  }
  return <Navigate to={getLandingPathByRole(role)} replace />;
};

/* ===========================
   App Content (Logic & Routes)
=========================== */

/**
 * 注意：必须将逻辑抽离到 AppInner，
 * 这样它才能在 App 里的 <Provider> 包裹下正常使用 useDispatch。
 */
const AppInner: React.FC = () => {
  const dispatch = useDispatch();

  useEffect(() => {
    // 设置全局 API 引用
    setStoreRef(store);
    
    // 初始化 Auth
    const t = setTimeout(() => {
      dispatch(initAuth() as any);
    }, 100);

    // 预加载数据
    preloadPopularData();

    return () => clearTimeout(t);
  }, [dispatch]);

  return (
    <Router>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          {/* ================= Public ================= */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              path="/email-verification"
              element={<EmailVerificationPage />}
            />
            <Route path="/assessment" element={<PublicAssessmentPage />} />
            <Route path="/intelligence" element={<PublicIntelligencePage />} />
            <Route path="/mentors" element={<MentorListPage />} />
            <Route path="/mentors/:id" element={<MentorDetailPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/resources" element={<ResourcesPage />} />
            <Route path="/resources/resume-tips" element={<ResumeTipsPage />} />
            <Route path="/resources/interview-guide" element={<InterviewGuidePage />} />
            <Route path="/resources/career-roadmaps" element={<CareerRoadmapsPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/become-a-mentor" element={<BecomeMentorPage />} />
          </Route>

          {/* ================= Shared (Authenticated) ================= */}
          <Route element={<ProtectedGate />}>
            <Route
              path="/dashboard"
              element={<RoleRedirect targetByRole={{ student: '/student' }} />}
            />
            <Route
              path="/dashboard/assessment"
              element={<RoleRedirect targetByRole={{ student: '/student/assessment' }} />}
            />
            <Route
              path="/dashboard/intelligence"
              element={<RoleRedirect targetByRole={{ student: '/student/intelligence' }} />}
            />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route
              path="/appointments"
              element={
                <RoleRedirect
                  targetByRole={{
                    student: '/student/appointments',
                    mentor: '/mentor/appointments',
                    staff: '/staff/appointments',
                    admin: '/admin/appointments',
                    superadmin: '/superadmin/appointments',
                  }}
                />
              }
            />
            <Route
              path="/appointments/create"
              element={<RoleRedirect targetByRole={{ student: '/student/appointments/create' }} />}
            />
            <Route path="/appointments/:id" element={<AppointmentDetailRedirect />} />
            <Route
              path="/appointments/:id/reschedule"
              element={<AppointmentDetailRedirect action="reschedule" />}
            />
            <Route
              path="/resumes"
              element={<RoleRedirect targetByRole={{ student: '/student/resumes' }} />}
            />
            <Route
              path="/resumes/upload"
              element={<RoleRedirect targetByRole={{ student: '/student/resumes/upload' }} />}
            />
            <Route path="/resumes/:id/analysis" element={<ResumeDetailRedirect />} />
            <Route
              path="/chat"
              element={
                <RoleRedirect
                  targetByRole={{
                    student: '/student/chat',
                    mentor: '/mentor/chat',
                  }}
                />
              }
            />
            <Route path="/chat/:id" element={<ChatRoomRedirect />} />
          </Route>

          {/* ================= Student ================= */}
          <Route element={<ProtectedGate />}>
            <Route element={<StudentRoute />}>
              <Route element={<StudentLayout />}>
                <Route path="/student" element={<StudentDashboardPage />} />
                <Route path="/student/assessment" element={<StudentAssessmentPage />} />
                <Route path="/student/assessment/:id" element={<ResumeAnalysisDetailPage />} />
                <Route path="/student/insights" element={<StudentInsightsPage />} />
                <Route path="/student/intelligence" element={<StudentIntelligencePage />} />
                <Route path="/student/mentors" element={<MentorListPage />} />
                <Route path="/student/mentors/:id" element={<MentorDetailPage />} />
                <Route path="/student/appointments" element={<StudentAppointmentsPage />} />
                <Route path="/student/appointments/create" element={<CreateAppointmentPage />} />
                <Route path="/student/appointments/:id" element={<AppointmentDetailPage />} />
                <Route path="/student/appointments/:id/reschedule" element={<RescheduleAppointmentPage />} />
                <Route path="/student/resumes" element={<ResumeListPage />} />
                <Route path="/student/resumes/upload" element={<UploadResumePage />} />
                <Route path="/student/resumes/:id/analysis" element={<ResumeAnalysisPage />} />
                <Route path="/student/chat" element={<ChatListPage />} />
                <Route path="/student/chat/:id" element={<ChatRoomPage />} />
                <Route path="/student/notifications" element={<NotificationsPage />} />
                <Route path="/student/profile" element={<StudentProfilePage />} />
              </Route>
            </Route>
          </Route>

          {/* ================= Mentor ================= */}
          <Route element={<ProtectedGate />}>
            <Route element={<MentorRoute />}>
              <Route element={<MentorLayout />}>
                <Route path="/mentor" element={<MentorDashboardPage />} />
                <Route path="/mentor/profile" element={<MentorProfilePage />} />
                <Route path="/mentor/availability" element={<MentorAvailabilityPage />} />
                <Route path="/mentor/appointments" element={<MentorAppointmentsPage />} />
                <Route path="/mentor/earnings" element={<MentorEarningsPage />} />
                <Route path="/mentor/feedback" element={<MentorFeedbackPage />} />
                <Route path="/mentor/resources" element={<MentorResourcesPage />} />
                <Route path="/mentor/chat" element={<ChatListPage />} />
                <Route path="/mentor/chat/:id" element={<ChatRoomPage />} />
                <Route path="/mentor/notifications" element={<NotificationsPage />} />
              </Route>
            </Route>
          </Route>

          {/* ================= Staff ================= */}
          <Route element={<ProtectedGate />}>
            <Route element={<StaffRoute />}>
              <Route element={<StaffLayout />}>
                <Route path="/staff" element={<StaffDashboardPage />} />
                <Route path="/staff/mentors" element={<StaffMentorApprovalsPage />} />
                <Route path="/staff/appointments" element={<StaffAppointmentsPage />} />
                <Route path="/staff/resumes" element={<StaffResumesPage />} />
                <Route path="/staff/content" element={<StaffContentManagementPage />} />
                <Route path="/staff/support" element={<StaffUserSupportPage />} />
                <Route path="/staff/reports" element={<StaffReportsPage />} />
                <Route path="/staff/notifications" element={<NotificationsPage />} />
              </Route>
            </Route>
          </Route>

          {/* ================= Admin ================= */}
          <Route element={<ProtectedGate />}>
            <Route element={<AdminRoute />}>
              <Route element={<AdminLayout />}>
                <Route path="/admin" element={<AdminDashboardPage />} />
                <Route path="/admin/users" element={<AdminUserManagementPage />} />
                <Route path="/admin/mentors" element={<AdminMentorsPage />} />
                <Route path="/admin/appointments" element={<AdminAppointmentsPage />} />
                <Route path="/admin/assessment" element={<AdminAssessmentPage />} />
                <Route path="/admin/jobs" element={<AdminJobsPage />} />
                <Route path="/admin/exports" element={<AdminExportsPage />} />
                <Route path="/admin/content" element={<AdminContentPage />} />
                <Route path="/admin/promotions" element={<AdminPromotionsPage />} />
                <Route path="/admin/payouts" element={<AdminPayoutsPage />} />
                <Route path="/analytics" element={<AnalyticsPage />} />
                <Route path="/admin/notifications" element={<NotificationsPage />} />
              </Route>
            </Route>
          </Route>

          {/* ================= SuperAdmin ================= */}
          <Route element={<ProtectedGate />}>
            <Route element={<SuperAdminRoute />}>
              <Route element={<SuperAdminLayout />}>
                <Route path="/superadmin" element={<CommandCenter />} />
                <Route path="/superadmin/users" element={<SuperAdminUsersPage />} />
                <Route path="/superadmin/mentors" element={<SuperAdminMentorsPage />} />
                <Route path="/superadmin/appointments" element={<SuperAdminAppointmentsPage />} />
                <Route path="/superadmin/assessment" element={<SuperAdminAssessmentPage />} />
                <Route path="/superadmin/jobs" element={<SuperAdminJobsPage />} />
                <Route path="/superadmin/system-console" element={<SuperAdminSystemPage />} />
                <Route path="/superadmin/system" element={<SuperAdminSystemSettingsPage />} />
                <Route path="/superadmin/analytics" element={<AnalyticsPage />} />
                <Route path="/superadmin/notifications" element={<NotificationsPage />} />
              </Route>
            </Route>
          </Route>

          {/* ================= Fallback ================= */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </Router>
  );
};

/* ===========================
   Root App Component
=========================== */

function App() {
  return (
    <ErrorBoundary>
      <Provider store={store}>
        <PersistGate loading={<LoadingSpinner />} persistor={persistor}>
          <ThemeProvider theme={theme}>
            <CssBaseline />
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <NotificationProvider>
                <AuthProvider>
                  <RoleProvider>
                    <SystemSettingsProvider>
                      <AppInner />
                    </SystemSettingsProvider>
                  </RoleProvider>
                </AuthProvider>
              </NotificationProvider>
            </LocalizationProvider>
          </ThemeProvider>
        </PersistGate>
      </Provider>
    </ErrorBoundary>
  );
}

export default App;
