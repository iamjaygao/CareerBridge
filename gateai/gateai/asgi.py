"""
ASGI config for gateai project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gateai.settings')

# Initialise Django before importing anything that touches models.
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.db import database_sync_to_async  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from chat.routing import websocket_urlpatterns  # noqa: E402
from kernel.policies.bus_power import is_bus_powered  # noqa: E402


class BusGatedWebSocket:
    """
    Refuse every WebSocket handshake while `bus` is OFF, before routing.

    GovernanceMiddleware only sees HTTP, so WebSockets need their own gate.
    While the bus is OFF no WebSocket route is reachable at all.
    """

    def __init__(self, inner, bus):
        self.inner = inner
        self.bus = bus

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'websocket' and not await database_sync_to_async(is_bus_powered)(self.bus):
            await receive()  # websocket.connect
            await send({'type': 'websocket.close', 'code': 4404})
            return
        await self.inner(scope, receive, send)


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # TODO(CHAT_BUS launch checklist): authentication and object-level checks
    # in the consumer before CHAT_BUS may be turned on.
    "websocket": BusGatedWebSocket(
        AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
        bus='CHAT_BUS',
    ),
})
