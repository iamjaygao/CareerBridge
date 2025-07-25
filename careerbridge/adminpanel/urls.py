from django.urls import path
from rest_framework.views import APIView   
from rest_framework.response import Response

class AdminPanelView(APIView):
    def get(self, request):
        return Response({'message': 'Admin Panel API is working!'})
    
urlpatterns = [
    path('', AdminPanelView.as_view(), name='adminpanel'),
]