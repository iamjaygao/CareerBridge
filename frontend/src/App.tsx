import React, { Suspense, lazy } from 'react';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import configureStore from './store/configureStore';
import MainLayout from './components/layout/MainLayout';
import ErrorBoundary from './components/common/ErrorBoundary';
import { NotificationProvider } from './components/common/NotificationProvider';
import { AuthProvider } from './contexts/AuthContext';
import LoadingSpinner from './components/common/LoadingSpinner';
import PerformanceMonitor from './components/common/PerformanceMonitor';
import theme from './theme';

// Lazy load pages for better performance
const LoginPage = lazy(() => import('./pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('./pages/auth/RegisterPage'));
const PasswordResetPage = lazy(() => import('./pages/auth/PasswordResetPage'));
const EmailVerificationPage = lazy(() => import('./pages/auth/EmailVerificationPage'));
const DashboardPage = lazy(() => import('./pages/dashboard/DashboardPage'));
const MentorListPage = lazy(() => import('./pages/mentors/MentorListPage'));
const MentorDetailPage = lazy(() => import('./pages/mentors/MentorDetailPage'));
const AppointmentListPage = lazy(() => import('./pages/appointments/AppointmentListPage'));
const CreateAppointmentPage = lazy(() => import('./pages/appointments/CreateAppointmentPage'));
const ResumeListPage = lazy(() => import('./pages/resumes/ResumeListPage'));
const UploadResumePage = lazy(() => import('./pages/resumes/UploadResumePage'));
const ResumeAnalysisPage = lazy(() => import('./pages/resumes/ResumeAnalysisPage'));
const ProfilePage = lazy(() => import('./pages/profile/ProfilePage'));
const SettingsPage = lazy(() => import('./pages/settings/SettingsPage'));
const AdminDashboardPage = lazy(() => import('./pages/admin/AdminDashboardPage'));
const UserManagementPage = lazy(() => import('./pages/admin/UserManagementPage'));
const MentorApplicationsPage = lazy(() => import('./pages/admin/MentorApplicationsPage'));
const AppointmentManagementPage = lazy(() => import('./pages/admin/AppointmentManagementPage'));
const SystemSettingsPage = lazy(() => import('./pages/admin/SystemSettingsPage'));
const NotFoundPage = lazy(() => import('./pages/error/NotFoundPage'));

const { store, persistor } = configureStore();

// Protected Route component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = localStorage.getItem('access_token');
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

function App() {
  return (
    <ErrorBoundary>
      <Provider store={store}>
        <PersistGate loading={<LoadingSpinner />} persistor={persistor}>
          <AuthProvider>
            <ThemeProvider theme={theme}>
              <CssBaseline />
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <NotificationProvider>
                  <Router>
                    <Suspense fallback={<LoadingSpinner />}>
                    <Routes>
                      {/* Public routes */}
                      <Route path="/login" element={<LoginPage />} />
                      <Route path="/register" element={<RegisterPage />} />
                      <Route path="/password-reset" element={<PasswordResetPage />} />
                      <Route path="/email-verification" element={<EmailVerificationPage />} />
                      
                      {/* Protected routes */}
                      <Route path="/dashboard" element={
                        <ProtectedRoute>
                          <MainLayout>
                            <DashboardPage />
                          </MainLayout>
                        </ProtectedRoute>
                      } />
                      
                      <Route path="/mentors" element={
                        <ProtectedRoute>
                          <MainLayout>
                            <MentorListPage />
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
                      
                      <Route path="/appointments" element={
                        <ProtectedRoute>
                          <MainLayout>
                            <AppointmentListPage />
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
                      
                      <Route path="/resumes" element={
                        <ProtectedRoute>
                          <MainLayout>
                            <ResumeListPage />
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
                      
                      <Route path="/admin" element={
                        <ProtectedRoute>
                          <MainLayout>
                            <AdminDashboardPage />
                          </MainLayout>
                        </ProtectedRoute>
                      } />
                      
                      <Route path="/admin/users" element={
                        <ProtectedRoute>
                          <MainLayout>
                            <UserManagementPage />
                          </MainLayout>
                        </ProtectedRoute>
                      } />
                      
                      <Route path="/admin/mentors/applications" element={
                        <ProtectedRoute>
                          <MainLayout>
                            <MentorApplicationsPage />
                          </MainLayout>
                        </ProtectedRoute>
                      } />
                      
                      <Route path="/admin/appointments" element={
                        <ProtectedRoute>
                          <MainLayout>
                            <AppointmentManagementPage />
                          </MainLayout>
                        </ProtectedRoute>
                      } />
                      
                      <Route path="/admin/settings" element={
                        <ProtectedRoute>
                          <MainLayout>
                            <SystemSettingsPage />
                          </MainLayout>
                        </ProtectedRoute>
                      } />
                      
                      {/* Default redirect */}
                      <Route path="/" element={<Navigate to="/dashboard" replace />} />
                      <Route path="*" element={<NotFoundPage />} />
                    </Routes>
                  </Suspense>
                </Router>
              </NotificationProvider>
              </LocalizationProvider>
            </ThemeProvider>
          </AuthProvider>
        </PersistGate>
      </Provider>
      <PerformanceMonitor />
    </ErrorBoundary>
  );
}

export default App;
