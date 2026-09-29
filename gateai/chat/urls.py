from django.urls import path, include
from rest_framework import routers
from rest_framework.permissions import IsAuthenticated
from rest_framework.routers import DefaultRouter
from . import views


class ChatAPIRootView(routers.APIRootView):
    permission_classes = [IsAuthenticated]


router = DefaultRouter()
router.APIRootView = ChatAPIRootView
router.register(r'rooms', views.ChatRoomViewSet, basename='chatroom')
router.register(r'messages', views.MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
] 