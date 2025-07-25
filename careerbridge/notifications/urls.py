from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response

class NotificationView(APIView):
    def get(self, request):
        return Response({'message': 'Notifications API is working!'})
    
urlpatterns = [
    path('', NotificationView.as_view(), name='notifications'),
]