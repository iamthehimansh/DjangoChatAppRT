import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    users_in_room = {}

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Add user to the room
        await self.add_user_to_room()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Broadcast the updated user count
        user_count = await self.get_room_user_count(self.room_name)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_count',
                'count': user_count
            }
        )

    async def disconnect(self, close_code):
        # Remove user from the room
        await self.remove_user_from_room()

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Broadcast the updated user count
        user_count = await self.get_room_user_count(self.room_name)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_count',
                'count': user_count
            }
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        id = text_data_json['id']
        # Broadcast the message to all channels in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'id': id
            }
        )

    async def chat_message(self, event):
        message = event['message']
        id = event['id']
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'id': id
        }))

    async def user_count(self, event):
        count = event['count']
        await self.send(text_data=json.dumps({
            'type': 'user_count',
            'count': count
        }))

    @database_sync_to_async
    def add_user_to_room(self):
        if self.room_name not in ChatConsumer.users_in_room:
            ChatConsumer.users_in_room[self.room_name] = set()
        ChatConsumer.users_in_room[self.room_name].add(self.channel_name)

    @database_sync_to_async
    def remove_user_from_room(self):
        if self.room_name in ChatConsumer.users_in_room:
            ChatConsumer.users_in_room[self.room_name].discard(self.channel_name)
            if not ChatConsumer.users_in_room[self.room_name]:
                del ChatConsumer.users_in_room[self.room_name]

    @classmethod
    @database_sync_to_async
    def get_room_user_count(cls, room_name):
        return len(cls.users_in_room.get(room_name, set()))
class OnlineConsumer(AsyncWebsocketConsumer):
    online_users = set()

    async def connect(self):
        self.user = self.scope['user']
        OnlineConsumer.online_users.add(self.user.username)
        await self.channel_layer.group_add("online_users", self.channel_name)
        await self.accept()
        await self.channel_layer.group_send("online_users", {
            "type": "user_status",
            "user": self.user.username,
            "status": "join",
            "online_users": list(OnlineConsumer.online_users)
        })

    async def disconnect(self, close_code):
        OnlineConsumer.online_users.discard(self.user.username)
        await self.channel_layer.group_discard("online_users", self.channel_name)
        await self.channel_layer.group_send("online_users", {
            "type": "user_status",
            "user": self.user.username,
            "status": "leave",
            "online_users": list(OnlineConsumer.online_users)
        })

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_status",
            "user": event["user"],
            "status": event["status"],
            "online_users": event["online_users"]
        }))