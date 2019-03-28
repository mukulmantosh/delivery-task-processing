from channels.generic.websocket import AsyncJsonWebsocketConsumer


class StoreTaskConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        await self.accept()
        self.user = self.scope["user"]

        if not self.user.is_anonymous:
            self.user_room_name = "store_task_notify_user_" + str(self.user.id)
            await self.channel_layer.group_add(
                self.user_room_name,
                self.channel_name
            )
            print(f"Added {self.channel_name} channel")

    async def disconnect(self, close_code):
        if not self.user.is_anonymous:
            await self.channel_layer.group_discard(self.user_room_name, self.channel_name)
            print(f"Removed {self.channel_name} channel")

    async def user_store_task_notify(self, event):
        await self.send_json(event)
        print(f"Got message {event} at {self.channel_name}")


class NotifyConsumer(AsyncJsonWebsocketConsumer):
    """
    Notify new orders to delivery boys.
    """

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("gossip", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("gossip", self.channel_name)

    async def user_gossip(self, event):
        await self.send_json(event)
