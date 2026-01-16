from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class PeerMockHealthView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            "ok": True,
            "service": "peer_mock",
            "ts": timezone.now().isoformat()
        })


class PeerMockStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            "bus": "PEER_MOCK_BUS",
            "state": "ON",
            "ts": timezone.now().isoformat()
        })


class PeerMockSessionsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response([])
