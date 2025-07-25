from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response


class ResumeView(APIView):
    def get(self, request):
        return Response({'message': 'Resumes API is working!'})
    
urlpatterns = [
    path('', ResumeView.as_view(), name='resumes'),
]