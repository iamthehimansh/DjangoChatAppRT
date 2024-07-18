import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    async def chat_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))

class OnlineConsumer(AsyncWebsocketConsumer):
    online_users = set()

    async def connect(self):
        self.user = self.scope['user']
        OnlineConsumer.online_users.add(self.user.username)
        await self.channel_layer.group_add("online_users", self.channel_name)
        await self.accept()
        await self.channel_layer.group_send("online_users", {
            "type": "user_join",
            "user": self.user.username,
            "online_users": list(OnlineConsumer.online_users)
        })

    async def disconnect(self, close_code):
        OnlineConsumer.online_users.discard(self.user.username)
        await self.channel_layer.group_discard("online_users", self.channel_name)
        await self.channel_layer.group_send("online_users", {
            "type": "user_leave",
            "user": self.user.username,
            "online_users": list(OnlineConsumer.online_users)
        })

    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_join",
            "user": event["user"],
            "online_users": event["online_users"]
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_leave",
            "user": event["user"],
            "online_users": event["online_users"]
        }))