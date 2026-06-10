import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_authenticated:
            await set_user_online(self.user)

        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if self.scope["user"].is_authenticated:
            await set_user_offline(self.scope["user"])

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        message_type = data.get("type")

        # 💬 normal message
        if message_type == "message":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": data["message"],
                    "sender": data["sender"]
                }
            )

        # ⌨️ typing indicator
        elif message_type == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_event",
                    "sender": data["sender"],
                    "is_typing": data["is_typing"]
                }
            )
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender']
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message']
        }))

    async def typing_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing",
            "sender": event["sender"],
            "is_typing": event["is_typing"]
        }))

@database_sync_to_async
def set_online(user):
    profile = user.profile
    profile.is_online = True
    profile.save()

@database_sync_to_async
def set_offline(user):
    profile = user.profile
    profile.is_online = False
    profile.last_seen = timezone.now()
    profile.save()


@database_sync_to_async
def set_user_online(user):
    profile = user.profile
    profile.is_online = True
    profile.save()

@database_sync_to_async
def set_user_offline(user):
    profile = user.profile
    profile.is_online = False
    profile.last_seen = timezone.now()
    profile.save()

# when message is received
from .models import Message, ChatRoom

@database_sync_to_async
def save_message(room_id, sender, message):
    room = ChatRoom.objects.get(id=room_id)
    return Message.objects.create(
        room=room,
        sender=sender,
        message=message
    )

@database_sync_to_async
def mark_as_read(room, user):
    Message.objects.filter(room=room).exclude(sender=user).update(is_read=True)


async def file_message(self, event):
    await self.send(text_data=json.dumps({
        "type": "file",
        "sender": event["sender"],
        "file": event["file"]
    }))