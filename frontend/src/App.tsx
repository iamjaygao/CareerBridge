import React, { Suspense, lazy } from 'react';
import { Provider, useSelector } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { store, persistor } from './store';
import { RootState } from './store';
import { useDispatch } from 'react-redux';
import { initAuth } from './store/slices/authSlice';
import { setStoreRef } from './services/api/client';
import PublicLayout from './components/layout/PublicLayout';
import DashboardLayout from './components/layout/DashboardLayout';
import MainLayout from './components/layout/MainLayout';
import AdminLayout from './components/layout/AdminLayout';
import SuperAdminLayout from './components/layout/SuperAdminLayout';
import StaffLayout from './components/layout/StaffLayout';
import StudentLayout from './components/layout/StudentLayout';
import MentorLayout from './components/layout/MentorLayout';
import AdminRoute from './components/admin/AdminRoute';
import StaffRoute from './components/staff/StaffRoute';
import StudentRoute from './components/student/StudentRoute';
import MentorRoute from './components/mentor/MentorRoute';
import ErrorBoundary from './components/common/ErrorBoundary';
import { NotificationProvider } from './components/common/NotificationProvider';
import { AuthProvider } from './contexts/AuthContext';
import { RoleProvider } from './contexts/RoleContext';
import { SystemSettingsProvider } from './contexts/SystemSettingsContext';
import LoadingSpinner from './components/common/LoadingSpinner';
import theme from './theme/theme';
import { preloadPopularData } from './services/api/searchService';

// Lazy load pages for better performance
const LandingPage = lazy(() => import('./pages/home/LandingPage'));
const LoginPage = lazy(() => import('./pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('./pages/auth/RegisterPage'));
const PasswordResetPage = lazy(() => import('./pages/auth/PasswordResetPage'));
const EmailVerificationPage = lazy(() => import('./pages/auth/EmailVerificationPage'));
const DashboardPage = lazy(() => import('./pages/dashboard/DashboardPage'));
const MentorListPage = lazy(() => import('./pages/mentors/MentorListPage'));
const MentorDetailPage = lazy(() => import('./pages/mentors/MentorDetailPage'));
const AppointmentListPage = lazy(() => import('./pages/appointments/AppointmentListPage'));
const CreateAppointmentPage = lazy(() => import('./pages/appointments/CreateAppointmentPage'));
const AssessmentPage = lazy(() => import('./pages/assessment/AssessmentPage'));
const AssessmentDashboardPage = lazy(() => import('./pages/dashboard/AssessmentDashboardPage'));
const IntelligencePage = lazy(() => import('./pages/intelligence/IntelligencePage'));
const PricingPage = lazy(() => import('./pages/pricing/PricingPage'));
const ResourcesPage = lazy(() => import('./pages/resources/ResourcesPage'));
const ResumeTipsPage = lazy(() => import('./pages/resources/ResumeTipsPage'));
const InterviewGuidePage = lazy(() => import('./pages/resources/InterviewGuidePage'));
const CareerRoadmapsPage = lazy(() => import('./pages/resources/CareerRoadmapsPage'));
const AboutPage = lazy(() => import('./pages/about/AboutPage'));
const ContactPage = lazy(() => import('./pages/contact/ContactPage'));
const BecomeMentorPage = lazy(() => import('./pages/become-mentor/BecomeMentorPage'));
const TermsPage = lazy(() => import('./pages/legal/TermsPage'));
const PrivacyPage = lazy(() => import('./pages/legal/PrivacyPage'));
const ResumeListPage = lazy(() => import('./pages/resumes/ResumeListPage'));
const PayoutsPage = lazy(() => import('./pages/admin/payouts/PayoutsPage'));
const PromotionsPage = lazy(() => import('./pages/admin/promotions/PromotionsPage'));
const ContentPage = lazy(() => import('./pages/admin/content/ContentPage'));
const MentorsPage = lazy(() => import('./pages/admin/mentors/MentorsPage'));
const StaffDashboardPage = lazy(() => import('./pages/staff/DashboardPage'));
const StaffMentorApprovalsPage = lazy(() => import('./pages/staff/mentors/MentorApprovalsPage'));
const StaffAppointmentsPage = lazy(() => import('./pages/staff/appointments/AppointmentsPage'));
const StaffContentPage = lazy(() => import('./pages/staff/content/ContentManagementPage'));
const StaffSupportPage = lazy(() => import('./pages/staff/support/UserSupportPage'));
const StaffReportsPage = lazy(() => import('./pages/staff/reports/ReportsPage'));
const StudentDashboardPage = lazy(() => import('./pages/student/DashboardPage'));
const StudentAssessmentPage = lazy(() => import('./pages/student/AssessmentPage'));
const StudentInsightsPage = lazy(() => import('./pages/student/InsightsPage'));
const StudentIntelligencePage = lazy(() => import('./pages/student/IntelligencePage'));
const StudentMentorsPage = lazy(() => import('./pages/student/MentorsPage'));
const StudentAppointmentsPage = lazy(() => import('./pages/student/AppointmentsPage'));
const StudentProfilePage = lazy(() => import('./pages/student/ProfilePage'));
const MentorDashboardPage = lazy(() => import('./pages/mentor/DashboardPage'));
const MentorProfilePage = lazy(() => import('./pages/mentor/ProfilePage'));
const MentorAvailabilityPage = lazy(() => import('./pages/mentor/AvailabilityPage'));
const MentorAppointmentsPage = lazy(() => import('./pages/mentor/AppointmentsPage'));
const MentorEarningsPage = lazy(() => import('./pages/mentor/EarningsPage'));
const MentorFeedbackPage = lazy(() => import('./pages/mentor/FeedbackPage'));
const MentorResourcesPage = lazy(() => import('./pages/mentor/ResourcesPage'));
const UploadResumePage = lazy(() => import('./pages/resumes/UploadResumePage'));
const ResumeAnalysisPage = lazy(() => import('./pages/resumes/ResumeAnalysisPage'));
const ProfilePage = lazy(() => import('./pages/profile/ProfilePage'));
const SettingsPage = lazy(() => import('./pages/settings/SettingsPage'));
const NotificationsPage = lazy(() => import('./pages/notifications/NotificationsPage'));
const ChatListPage = lazy(() => import('./pages/chat/ChatListPage'));
const ChatRoomPage = lazy(() => import('./pages/chat/ChatRoomPage'));
const AdminDashboardPage = lazy(() => import('./pages/admin/AdminDashboardPage'));
const UserManagementPage = lazy(() => import('./pages/admin/UserManagementPage'));
const MentorApplicationsPage = lazy(() => import('./pages/admin/MentorApplicationsPage'));
const AppointmentManagementPage = lazy(() => import('./pages/admin/AppointmentManagementPage'));
const SystemSettingsPage = lazy(() => import('./pages/admin/system/SystemSettingsPage'));
const SuperAdminDashboardPage = lazy(() => import('./pages/superadmin/SuperAdminDashboard'));
const CommandCenter = lazy(() => import('./pages/superadmin/CommandCenter'));
const AnalyticsPage = lazy(() => import('./pages/analytics/AnalyticsPage'));
const SuperAdminUsersPage = lazy(() => import('./pages/superadmin/UsersPage'));
const SuperAdminMentorsPage = lazy(() => import('./pages/superadmin/MentorsPage'));
const SuperAdminAppointmentsPage = lazy(() => import('./pages/superadmin/AppointmentsPage'));
const SuperAdminAssessmentPage = lazy(() => import('./pages/superadmin/AssessmentPage'));
const SuperAdminJobsPage = lazy(() => import('./pages/superadmin/JobsPage'));
const SuperAdminSystemPage = lazy(() => import('./pages/superadmin/SystemPage'));
const AdminAssessmentPage = lazy(() => import('./pages/admin/AssessmentPage'));
const AdminJobsPage = lazy(() => import('./pages/admin/JobsPage'));
const NotFoundPage = lazy(() => import('./pages/error/NotFoundPage'));
const PaymentDemoPage = lazy(() => import('./pages/payments/PaymentDemoPage'));

// Store and persistor are already imported

// Protected Route component - requires authentication
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, authLoaded } = useSelector((state: RootState) => state.auth);
  
  // Wait for Redux to fully load localStorage-auth state
  if (!authLoaded) return null;
  
  // After loaded, allow or redirect
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// Public Route component - allows public access but shows different content for authenticated users
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};

function App() {
  const dispatch = useDispatch();

  // Set store reference for apiClient to update Redux state after token refresh
  React.useEffect(() => {
    setStoreRef(store);
  }, []);

  // Initialize auth state on app mount (after Redux Persist rehydration)
  React.useEffect(() => {
    // Wait a tick to ensure PersistGate has completed rehydration
    const timer = setTimeout(() => {
      dispatch(initAuth() as any);
    }, 100);
    return () => clearTimeout(timer);
  }, [dispatch]);

  // Pre-load popular data on app initialization
  React.useEffect(() => {
    preloadPopularData();
  }, []);

  return (
    <ErrorBoundary>
      <Provider store={store}>
        <PersistGate loading={<LoadingSpinner />} persistor={persistor}>
          <AuthProvider>
            <RoleProvider>
              <SystemSettingsProvider>
                <ThemeProvider theme={theme}>
                <CssBaseline />
                <LocalizationProvider dateAdapter={AdapterDateFns}>
                  <NotificationProvider>
                    <Router>
                      <Suspense fallback={<LoadingSpinner />}>
                        <Routes>
                        {/* Public Layout Route - for marketing pages with PublicHeader and PublicFooter */}
                        <Route element={<PublicLayout />}>
                          {/* Public routes */}
                          <Route path="/" element={<LandingPage />} />
                          <Route path="/login" element={<LoginPage />} />
                          <Route path="/register" element={<RegisterPage />} />
                          <Route path="/password-reset" element={<PasswordResetPage />} />
                          <Route path="/email-verification" element={<EmailVerificationPage />} />
                          
                          <Route path="/mentors" element={<MentorListPage />} />
                          <Route path="/assessment" element={<AssessmentPage />} />
                          <Route path="/intelligence" element={<IntelligencePage />} />
                          <Route path="/pricing" element={<PricingPage />} />
                          <Route path="/resources" element={<ResourcesPage />} />
                          <Route path="/resources/resume-tips" element={<ResumeTipsPage />} />
                          <Route path="/resources/interview-guide" element={<InterviewGuidePage />} />
                          <Route path="/resources/career-roadmaps" element={<CareerRoadmapsPage />} />
                          <Route path="/about" element={<AboutPage />} />
                          <Route path="/contact" element={<ContactPage />} />
                          <Route path="/become-a-mentor" element={<BecomeMentorPage />} />
                          <Route path="/terms" element={<TermsPage />} />
                          <Route path="/privacy" element={<PrivacyPage />} />
                          <Route path="/appointments" element={<AppointmentListPage />} />
                          <Route path="/resumes" element={<Navigate to="/assessment" replace />} />
                        </Route>

                        {/* Dashboard Layout Route - for logged-in users with DashboardHeader only (NO footer) */}
                        <Route element={<DashboardLayout />}>
                          {/* Dashboard routes */}
                          <Route path="/dashboard" element={
                            <ProtectedRoute>
                              <MainLayout>
                                <DashboardPage />
                              </MainLayout>
                            </ProtectedRoute>
                          } />
                          
                          <Route path="/dashboard/assessment" element={
                            <ProtectedRoute>
                              <MainLayout>
                                <AssessmentDashboardPage />
                              </MainLayout>
                            </ProtectedRoute>
                          } />
                          
                          <Route path="/mentors/:id" element={
                            <ProtectedRoute>
                              <MainLayout>
                                <MentorDetailPage />
                              </MainLayout>
                            </ProtectedRoute>
                          } />
                          
                          <Route path="/mentors/:id/book" element={
                            <ProtectedRoute>
                              <MainLayout>
                                <MentorDetailPage initialTab="booking" />
                              </MainLayout>
                            </ProtectedRoute>
                          } />
                          
                          <Route path="/appointments/create" element={
                            <ProtectedRoute>
                              <MainLayout>
                                <CreateAppointmentPage />
                              </MainLayout>
                            </ProtectedRoute>
                          } />
                          
                          <Route path="/resumes/upload" element={
                            <ProtectedRoute>
                              <MainLayout>
                                <UploadResumePage />
                              </MainLayout>
                            </ProtectedRoute>
                          } />
                          
                          <Route path="/resumes/:id/analysis" element={
                            <ProtectedRoute>
                              <MainLayout>
                                <ResumeAnalysisPage />
                              </MainLayout>
                            </ProtectedRoute>
                          } />
                          
                          <Route path="/profile" element={
                            <ProtectedRoute>
                              <MainLayout>
                                <ProfilePage />
                              </MainLayout>
                            </ProtectedRoute>
                          } />
                          
                          <Route path="/settings" element={
                            <ProtectedRoute>
                              <MainLayout>
                                <SettingsPage />
                              </MainLayout>
                            </ProtectedRoute>
                          } />

                          <Route path="/notifications" element={
                            <ProtectedRoute>
                              <MainLayout>
                                <NotificationsPage />
                              </MainLayout>
                            </ProtectedRoute>
                          } />

                          <Route path="/payments/demo" element={
                            <ProtectedRoute>
                              <MainLayout>
                                <PaymentDemoPage />
                              </MainLayout>
                            </ProtectedRoute>
                          } />
                          
                          <Route path="/chat" element={
                            <ProtectedRoute>
                              <MainLayout>
                                <ChatListPage />
                              </MainLayout>
                            </ProtectedRoute>
                          } />
                          
                          <Route path="/chat/:roomId" element={
                            <ProtectedRoute>
                              <MainLayout>
                                <ChatRoomPage />
                              </MainLayout>
                            </ProtectedRoute>
                          } />
                          
                          {/* Default redirect for authenticated users */}
                          <Route path="*" element={<NotFoundPage />} />
                        </Route>

                        {/* SuperAdmin Routes - Outside DashboardLayout to avoid duplicate header */}
                        <Route path="/superadmin" element={
                          <ProtectedRoute>
                            <SuperAdminLayout>
                              <CommandCenter />
                            </SuperAdminLayout>
                          </ProtectedRoute>
                        } />
                        
                        {/* Analytics Route - Accessible to SuperAdmin and Admin */}
                        <Route path="/analytics" element={
                          <ProtectedRoute>
                            <SuperAdminLayout>
                              <AnalyticsPage />
                            </SuperAdminLayout>
                          </ProtectedRoute>
                        } />

                        <Route path="/superadmin/users" element={
                          <ProtectedRoute>
                            <SuperAdminLayout>
                              <SuperAdminUsersPage />
                            </SuperAdminLayout>
                          </ProtectedRoute>
                        } />

                        <Route path="/superadmin/mentors" element={
                          <ProtectedRoute>
                            <SuperAdminLayout>
                              <SuperAdminMentorsPage />
                            </SuperAdminLayout>
                          </ProtectedRoute>
                        } />

                        <Route path="/superadmin/appointments" element={
                          <ProtectedRoute>
                            <SuperAdminLayout>
                              <SuperAdminAppointmentsPage />
                            </SuperAdminLayout>
                          </ProtectedRoute>
                        } />

                        <Route path="/superadmin/assessment" element={
                          <ProtectedRoute>
                            <SuperAdminLayout>
                              <SuperAdminAssessmentPage />
                            </SuperAdminLayout>
                          </ProtectedRoute>
                        } />

                        <Route path="/superadmin/jobs" element={
                          <ProtectedRoute>
                            <SuperAdminLayout>
                              <SuperAdminJobsPage />
                            </SuperAdminLayout>
                          </ProtectedRoute>
                        } />

                        <Route path="/superadmin/system" element={
                          <ProtectedRoute>
                            <SuperAdminLayout>
                              <SuperAdminSystemPage />
                            </SuperAdminLayout>
                          </ProtectedRoute>
                        } />

                        {/* Role-specific layouts - These have their own topbars and sidebars, NO DashboardLayout wrapper */}
                        {/* Admin routes with AdminLayout - NO public Header/Footer - RBAC Protected */}
                        <Route path="/admin" element={
                          <AdminRoute>
                            <AdminLayout>
                              <AdminDashboardPage />
                            </AdminLayout>
                          </AdminRoute>
                        } />
                        
                        <Route path="/admin/users" element={
                          <AdminRoute>
                            <AdminLayout>
                              <UserManagementPage />
                            </AdminLayout>
                          </AdminRoute>
                        } />
                        
                        <Route path="/admin/mentors" element={
                          <AdminRoute>
                            <AdminLayout>
                              <MentorsPage />
                            </AdminLayout>
                          </AdminRoute>
                        } />
                        
                        <Route path="/admin/mentors/applications" element={
                          <AdminRoute>
                            <AdminLayout>
                              <MentorApplicationsPage />
                            </AdminLayout>
                          </AdminRoute>
                        } />
                        
                        <Route path="/admin/appointments" element={
                          <AdminRoute>
                            <AdminLayout>
                              <AppointmentManagementPage />
                            </AdminLayout>
                          </AdminRoute>
                        } />
                        
                        <Route path="/admin/payouts" element={
                          <AdminRoute>
                            <AdminLayout>
                              <PayoutsPage />
                            </AdminLayout>
                          </AdminRoute>
                        } />
                        
                        <Route path="/admin/promotions" element={
                          <AdminRoute>
                            <AdminLayout>
                              <PromotionsPage />
                            </AdminLayout>
                          </AdminRoute>
                        } />
                        
                        <Route path="/admin/content" element={
                          <AdminRoute>
                            <AdminLayout>
                              <ContentPage />
                            </AdminLayout>
                          </AdminRoute>
                        } />
                        
                        <Route path="/admin/assessment" element={
                          <AdminRoute>
                            <AdminLayout>
                              <AdminAssessmentPage />
                            </AdminLayout>
                          </AdminRoute>
                        } />
                        
                        <Route path="/admin/jobs" element={
                          <AdminRoute>
                            <AdminLayout>
                              <AdminJobsPage />
                            </AdminLayout>
                          </AdminRoute>
                        } />
                        
                        {/* System Settings removed from Admin - only for SuperAdmin */}
                        {/* Legacy /admin/settings redirect */}
                        <Route path="/admin/settings" element={
                          <AdminRoute>
                            <Navigate to="/admin" replace />
                          </AdminRoute>
                        } />
                        
                        <Route path="/admin/system" element={
                          <AdminRoute>
                            <Navigate to="/admin" replace />
                          </AdminRoute>
                        } />

                        {/* Staff routes with StaffLayout - NO public Header/Footer - RBAC Protected */}
                        <Route path="/staff" element={
                          <StaffRoute>
                            <StaffLayout>
                              <StaffDashboardPage />
                            </StaffLayout>
                          </StaffRoute>
                        } />
                        
                        <Route path="/staff/mentors" element={
                          <StaffRoute>
                            <StaffLayout>
                              <StaffMentorApprovalsPage />
                            </StaffLayout>
                          </StaffRoute>
                        } />
                        
                        <Route path="/staff/appointments" element={
                          <StaffRoute>
                            <StaffLayout>
                              <StaffAppointmentsPage />
                            </StaffLayout>
                          </StaffRoute>
                        } />
                        
                        <Route path="/staff/content" element={
                          <StaffRoute>
                            <StaffLayout>
                              <StaffContentPage />
                            </StaffLayout>
                          </StaffRoute>
                        } />
                        
                        <Route path="/staff/support" element={
                          <StaffRoute>
                            <StaffLayout>
                              <StaffSupportPage />
                            </StaffLayout>
                          </StaffRoute>
                        } />
                        
                        <Route path="/staff/reports" element={
                          <StaffRoute>
                            <StaffLayout>
                              <StaffReportsPage />
                            </StaffLayout>
                          </StaffRoute>
                        } />

                        {/* Student routes with StudentLayout - NO public Header/Footer - RBAC Protected */}
                        <Route path="/student" element={
                          <StudentRoute>
                            <StudentLayout>
                              <StudentDashboardPage />
                            </StudentLayout>
                          </StudentRoute>
                        } />
                        
                        <Route path="/student/assessment" element={
                          <StudentRoute>
                            <StudentLayout>
                              <StudentAssessmentPage />
                            </StudentLayout>
                          </StudentRoute>
                        } />
                        
                        <Route path="/student/insights" element={
                          <StudentRoute>
                            <StudentLayout>
                              <StudentInsightsPage />
                            </StudentLayout>
                          </StudentRoute>
                        } />
                        
                        <Route path="/student/intelligence" element={
                          <StudentRoute>
                            <StudentLayout>
                              <StudentIntelligencePage />
                            </StudentLayout>
                          </StudentRoute>
                        } />
                        
                        <Route path="/student/mentors" element={
                          <StudentRoute>
                            <StudentLayout>
                              <StudentMentorsPage />
                            </StudentLayout>
                          </StudentRoute>
                        } />
                        
                        <Route path="/student/appointments" element={
                          <StudentRoute>
                            <StudentLayout>
                              <StudentAppointmentsPage />
                            </StudentLayout>
                          </StudentRoute>
                        } />
                        
                        <Route path="/student/profile" element={
                          <StudentRoute>
                            <StudentLayout>
                              <StudentProfilePage />
                            </StudentLayout>
                          </StudentRoute>
                        } />

                        {/* Mentor routes with MentorLayout - NO public Header/Footer - RBAC Protected */}
                        <Route path="/mentor" element={
                          <MentorRoute>
                            <MentorLayout>
                              <MentorDashboardPage />
                            </MentorLayout>
                          </MentorRoute>
                        } />
                        
                        <Route path="/mentor/profile" element={
                          <MentorRoute>
                            <MentorLayout>
                              <MentorProfilePage />
                            </MentorLayout>
                          </MentorRoute>
                        } />
                        
                        <Route path="/mentor/availability" element={
                          <MentorRoute>
                            <MentorLayout>
                              <MentorAvailabilityPage />
                            </MentorLayout>
                          </MentorRoute>
                        } />
                        
                        <Route path="/mentor/appointments" element={
                          <MentorRoute>
                            <MentorLayout>
                              <MentorAppointmentsPage />
                            </MentorLayout>
                          </MentorRoute>
                        } />
                        
                        <Route path="/mentor/earnings" element={
                          <MentorRoute>
                            <MentorLayout>
                              <MentorEarningsPage />
                            </MentorLayout>
                          </MentorRoute>
                        } />
                        
                        <Route path="/mentor/feedback" element={
                          <MentorRoute>
                            <MentorLayout>
                              <MentorFeedbackPage />
                            </MentorLayout>
                          </MentorRoute>
                        } />
                        
                        <Route path="/mentor/resources" element={
                          <MentorRoute>
                            <MentorLayout>
                              <MentorResourcesPage />
                            </MentorLayout>
                          </MentorRoute>
                        } />
                      </Routes>
                        </Suspense>
                      </Router>
                    </NotificationProvider>
                  </LocalizationProvider>
                </ThemeProvider>
              </SystemSettingsProvider>
            </RoleProvider>
          </AuthProvider>
        </PersistGate>
      </Provider>
    </ErrorBoundary>
  );
}

export default App;
