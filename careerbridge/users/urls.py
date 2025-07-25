from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from . views import RegisterView


class UserView(APIView):
    def get(self, request):
        return Response({'message' : "Users API is working!"})

urlpatterns = [
    path('', UserView.as_view(), name='users'),
    path('register/', RegisterView.as_view(), name='register'),
]