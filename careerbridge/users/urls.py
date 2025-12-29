from django.urls import path
from .views import (
    RegisterView, LoginView, UserView, UserSettingsView,
    PasswordChangeView, UsernameChangeStatusView, AvatarUploadView, RefreshTokenView,
    ResendVerificationView, RequestVerificationView, EmailVerificationView,
    PasswordResetRequestView, PasswordResetView, PasswordResetConfirmView,
)
from dashboard.views.student import DashboardView

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    path('request-verification/', RequestVerificationView.as_view(), name='request-verification'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('reset-password/<uuid:token>/', PasswordResetView.as_view(), name='reset-password'),
    path('me/', UserView.as_view(), name='user-profile'),
    path('settings/', UserSettingsView.as_view(), name='user-settings'),
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('username-change-status/', UsernameChangeStatusView.as_view(), name='username-change-status'),
    path('avatar/', AvatarUploadView.as_view(), name='upload-avatar'),
    path('dashboard/stats/', DashboardView.as_view(), name='dashboard-stats'),
]
