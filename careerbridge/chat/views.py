from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import models
from .models import ChatRoom, Message, ChatParticipant
from .serializers import ChatRoomSerializer, MessageSerializer, ChatParticipantSerializer


class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(
            models.Q(user=user) | models.Q(mentor=user)
        ).filter(is_active=True)

    def perform_create(self, serializer):
        user = self.request.user
        mentor_id = self.request.data.get('mentor_id')
        
        # Check if chat room already exists
        existing_room = ChatRoom.objects.filter(
            user=user, mentor_id=mentor_id, is_active=True
        ).first()
        
        if existing_room:
            serializer.instance = existing_room
        else:
            serializer.save(user=user)

    @action(detail=True, methods=['post'])
    def mark_messages_read(self, request, pk=None):
        chat_room = self.get_object()
        user = request.user
        
        # Mark all unread messages as read
        unread_messages = Message.objects.filter(
            chat_room=chat_room,
            is_read=False
        ).exclude(sender=user)
        
        for message in unread_messages:
            message.mark_as_read()
        
        return Response({'status': 'messages marked as read'})

    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        chat_room = self.get_object()
        participants = ChatParticipant.objects.filter(chat_room=chat_room)
        serializer = ChatParticipantSerializer(participants, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            chat_room__user=user
        ) | Message.objects.filter(
            chat_room__mentor=user
        )

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        message = self.get_object()
        message.mark_as_read()
        return Response({'status': 'message marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        user = request.user
        count = Message.objects.filter(
            chat_room__user=user,
            is_read=False
        ).exclude(sender=user).count()
        
        count += Message.objects.filter(
            chat_room__mentor=user,
            is_read=False
        ).exclude(sender=user).count()
        
        return Response({'unread_count': count}) 