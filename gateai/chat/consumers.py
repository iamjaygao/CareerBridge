import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ChatRoom, Message, ChatParticipant
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the connection
        await self.accept()

        # Update participant status
        await self.update_participant_status(True)

    async def disconnect(self, close_code):
        # Update participant status
        await self.update_participant_status(False)

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'chat_message')
        
        if message_type == 'chat_message':
            message = text_data_json['message']
            sender_id = text_data_json['sender_id']
            
            # Save message to database
            saved_message = await self.save_message(message, sender_id)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': sender_id,
                    'sender_name': saved_message['sender_name'],
                    'timestamp': saved_message['timestamp'],
                    'message_id': saved_message['id']
                }
            )
        elif message_type == 'typing':
            # Handle typing indicator
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'user_id': text_data_json['user_id'],
                    'is_typing': text_data_json['is_typing']
                }
            )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))

    async def user_typing(self, event):
        # Send typing indicator to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'user_typing',
            'user_id': event['user_id'],
            'is_typing': event['is_typing']
        }))

    @database_sync_to_async
    def save_message(self, message, sender_id):
        try:
            chat_room = ChatRoom.objects.get(id=self.room_name)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            sender = User.objects.get(id=sender_id)
            
            message_obj = Message.objects.create(
                chat_room=chat_room,
                sender=sender,
                content=message
            )
            
            return {
                'id': message_obj.id,
                'sender_name': sender.username,
                'timestamp': message_obj.created_at.isoformat()
            }
        except (ChatRoom.DoesNotExist, User.DoesNotExist):
            return None

    @database_sync_to_async
    def update_participant_status(self, is_online):
        try:
            user = self.scope['user']
            if isinstance(user, AnonymousUser):
                return
            
            chat_room = ChatRoom.objects.get(id=self.room_name)
            participant, created = ChatParticipant.objects.get_or_create(
                user=user,
                chat_room=chat_room
            )
            participant.is_online = is_online
            participant.last_seen = timezone.now()
            participant.save()
        except ChatRoom.DoesNotExist:
            pass 