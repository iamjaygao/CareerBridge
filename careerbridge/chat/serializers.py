from rest_framework import serializers
from .models import ChatRoom, Message, ChatParticipant


class ChatRoomSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    mentor_name = serializers.CharField(source='mentor.username', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['id', 'user', 'mentor', 'user_name', 'mentor_name', 
                 'created_at', 'updated_at', 'is_active', 'last_message', 'unread_count']
        read_only_fields = ['created_at', 'updated_at']

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'content': last_msg.content[:100],
                'sender': last_msg.sender.username,
                'created_at': last_msg.created_at,
                'message_type': last_msg.message_type
            }
        return None

    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    sender_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'chat_room', 'sender', 'sender_name', 'sender_avatar',
                 'message_type', 'content', 'file', 'created_at', 'is_read']
        read_only_fields = ['created_at', 'is_read']

    def get_sender_avatar(self, obj):
        # Placeholder for avatar URL
        return None

    def create(self, validated_data):
        message = Message.objects.create(**validated_data)
        # Update chat room's updated_at timestamp
        message.chat_room.save()
        return message


class ChatParticipantSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.SerializerMethodField()

    class Meta:
        model = ChatParticipant
        fields = ['id', 'user', 'user_name', 'user_avatar', 'chat_room',
                 'is_online', 'last_seen', 'joined_at']
        read_only_fields = ['joined_at']

    def get_user_avatar(self, obj):
        # Placeholder for avatar URL
        return None 