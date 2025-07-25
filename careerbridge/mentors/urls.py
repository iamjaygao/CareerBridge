from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response

class MentorView(APIView): 
    def get(self, request):
        return Response({'message': 'Mentors API is working!'})
    
urlpatterns = [
    path('', MentorView.as_view(), name='mentors'),
]