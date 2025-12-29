import React, { Suspense, lazy, useEffect } from 'react';
import { Provider, useDispatch, useSelector } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  Outlet,
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
import { getLandingPathByRole } from './utils/roleLanding';

/* ===========================
   Lazy Pages
=========================== */
// Public
const LandingPage = lazy(() => import('./pages/home/LandingPage'));
const LoginPage = lazy(() => import('./pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('./pages/auth/RegisterPage'));
const EmailVerificationPage = lazy(() => import('./pages/auth/EmailVerificationPage'));

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
const StaffContentManagementPage = lazy(() => import('./pages/staff/content/ContentManagementPage'));
const StaffUserSupportPage = lazy(() => import('./pages/staff/support/UserSupportPage'));
const StaffReportsPage = lazy(() => import('./pages/staff/reports/ReportsPage'));

// Admin
const AdminDashboardPage = lazy(() => import('./pages/admin/AdminDashboardPage'));

// SuperAdmin
const CommandCenter = lazy(() => import('./pages/superadmin/CommandCenter'));

// Notifications (shared)
const NotificationsPage = lazy(() => import('./pages/notifications/NotificationsPage'));

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
                <Route path="/admin/notifications" element={<NotificationsPage />} />
              </Route>
            </Route>
          </Route>

          {/* ================= SuperAdmin ================= */}
          <Route element={<ProtectedGate />}>
            <Route element={<SuperAdminLayout />}>
              <Route path="/superadmin" element={<CommandCenter />} />
              <Route path="/superadmin/notifications" element={<NotificationsPage />} />
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
