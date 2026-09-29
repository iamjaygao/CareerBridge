from django.urls import path
from .views import (
    CurrentRoundView, MetaView, PeerMockHealthView, PeerMockSessionsView, PeerMockStatusView, ProfileView,
    RegistrationView,
)

urlpatterns = [
    path('health/', PeerMockHealthView.as_view(), name='peer_mock_health'),
    path('status/', PeerMockStatusView.as_view(), name='peer_mock_status'),
    path('sessions/', PeerMockSessionsView.as_view(), name='peer_mock_sessions'),
    path('meta/', MetaView.as_view(), name='peer_mock_meta'),
    path('me/profile/', ProfileView.as_view(), name='peer_mock_profile'),
    path('rounds/current/', CurrentRoundView.as_view(), name='peer_mock_current_round'),
    path('rounds/<uuid:round_id>/registration/', RegistrationView.as_view(), name='peer_mock_registration'),
]
