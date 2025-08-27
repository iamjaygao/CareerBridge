from django.urls import path
from .views import (
    RegisterView, LoginView, UserView,
    PasswordChangeView, UsernameChangeStatusView, AvatarUploadView, RefreshTokenView,
    EmailVerificationView, ResendVerificationView, PasswordResetRequestView, 
    PasswordResetView, UsernameRecoveryView, DashboardView
)

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('verify-email/<uuid:token>/', EmailVerificationView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('reset-password/<uuid:token>/', PasswordResetView.as_view(), name='reset-password'),
    path('username-recovery/', UsernameRecoveryView.as_view(), name='username-recovery'),
    path('me/', UserView.as_view(), name='user-profile'),
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('username-change-status/', UsernameChangeStatusView.as_view(), name='username-change-status'),
    path('avatar/', AvatarUploadView.as_view(), name='upload-avatar'),
    path('dashboard/stats/', DashboardView.as_view(), name='dashboard-stats'),
]