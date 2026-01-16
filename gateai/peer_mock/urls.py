from django.urls import path
from .views import PeerMockHealthView, PeerMockStatusView, PeerMockSessionsView

urlpatterns = [
    path('health/', PeerMockHealthView.as_view(), name='peer_mock_health'),
    path('status/', PeerMockStatusView.as_view(), name='peer_mock_status'),
    path('sessions/', PeerMockSessionsView.as_view(), name='peer_mock_sessions'),
]
