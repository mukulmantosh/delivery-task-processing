from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from store.consumers import StoreTaskConsumer, NotifyConsumer
from channels.auth import AuthMiddlewareStack

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("store-task-notify/", StoreTaskConsumer),
            path("new-order-notify/", NotifyConsumer),

        ])
    ),
})
