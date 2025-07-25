from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response

class AppointmentView(APIView):
    def get(self, request):
        return Response({'message': 'Appointments API is working!'})
    
urlpatterns = [
    path('', AppointmentView.as_view(), name='appointments'),
]