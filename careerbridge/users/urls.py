from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from . views import RegisterView, LoginView, UserView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', UserView.as_view(), name='user-profile'),
]