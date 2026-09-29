"""
Chat is its own module behind CHAT_BUS (default OFF).

- HTTP /api/v1/chat/ and the chat notification task are gated by CHAT_BUS.
- While CHAT_BUS is OFF no WebSocket route is reachable: connections are
  refused before routing, whoever the caller is.
- Booking (/api/v1/decision-slots/) belongs to the mentor module (MENTOR_BUS).
"""

from asgiref.sync import async_to_sync
from asgiref.testing import ApplicationCommunicator
from django.test import SimpleTestCase, TransactionTestCase, override_settings

from kernel.governance.models import BusPowerState
from kernel.policies.bus_power import BUS_POWER_DEFAULTS, invalidate_cache, resolve_bus

IN_MEMORY_LAYER = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}


def ws_connects(app, path):
    """True if the ASGI app accepts a WebSocket handshake on `path`.

    Minimal client (channels.testing needs daphne, which isn't a dependency).
    """
    async def attempt():
        scope = {'type': 'websocket', 'path': path, 'raw_path': path.encode(), 'query_string': b'',
                 'headers': [(b'host', b'testserver')], 'subprotocols': [], 'client': ('127.0.0.1', 1),
                 'server': ('testserver', 80)}
        comm = ApplicationCommunicator(app, scope)
        await comm.send_input({'type': 'websocket.connect'})
        try:
            message = await comm.receive_output(timeout=5)
        finally:
            await comm.send_input({'type': 'websocket.disconnect', 'code': 1000})
            try:
                await comm.wait(timeout=1)
            except Exception:
                pass
        return message['type'] == 'websocket.accept'
    return async_to_sync(attempt)()


class ChatBusMappingTest(SimpleTestCase):

    def test_chat_has_its_own_bus_off_by_default(self):
        self.assertEqual(BUS_POWER_DEFAULTS.get('CHAT_BUS'), 'OFF')

    def test_routes_map_to_their_module_bus(self):
        expected = {
            '/api/v1/chat/': 'CHAT_BUS',
            '/api/v1/chat/rooms/': 'CHAT_BUS',
            '/ws/chat/lobby/': 'CHAT_BUS',
            '/api/v1/decision-slots/lock-slot/': 'MENTOR_BUS',
            '/api/v1/decision-slots/time-slots/': 'MENTOR_BUS',
        }
        for path, bus in expected.items():
            with self.subTest(path=path):
                self.assertEqual(resolve_bus(path), bus)

    def test_chat_notification_task_is_gated_by_chat_bus(self):
        from chat.tasks import notify_staff_unanswered_chats
        self.assertEqual(notify_staff_unanswered_chats.required_bus, 'CHAT_BUS')


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYER)
class ChatWebSocketGateTest(TransactionTestCase):

    def setUp(self):
        BusPowerState.objects.bulk_create([BusPowerState(bus_name=n, state=s) for n, s in BUS_POWER_DEFAULTS.items()])
        invalidate_cache()
        self.addCleanup(invalidate_cache)

    def connect(self, path='/ws/chat/lobby/'):
        from gateai.asgi import application
        return ws_connects(application, path)

    def test_anonymous_cannot_connect_while_chat_bus_is_off(self):
        BusPowerState.objects.filter(bus_name='CHAT_BUS').update(state='OFF')  # OFF (or absent = OFF)
        invalidate_cache()
        self.assertFalse(self.connect(), 'a WebSocket must not open while CHAT_BUS is OFF')

    def test_no_room_is_reachable_while_chat_bus_is_off(self):
        for path in ('/ws/chat/lobby/', '/ws/chat/1/', '/ws/chat/staff/'):
            with self.subTest(path=path):
                self.assertFalse(self.connect(path))


class ChatBusGateUnitTest(TransactionTestCase):
    """The gate delegates to the chat routes only while CHAT_BUS is ON."""

    def test_gate_delegates_only_when_bus_is_on(self):
        from gateai.asgi import BusGatedWebSocket

        calls = []

        async def inner(scope, receive, send):
            calls.append(scope['path'])
            await send({'type': 'websocket.accept'})

        gate = BusGatedWebSocket(inner, bus='CHAT_BUS')

        def run():
            return ws_connects(gate, '/ws/chat/lobby/')

        for state, expect_connected in (('OFF', False), ('ON', True)):
            with self.subTest(state=state):
                BusPowerState.objects.update_or_create(bus_name='CHAT_BUS', defaults={'state': state})
                invalidate_cache()
                calls.clear()
                self.assertEqual(run(), expect_connected)
                self.assertEqual(bool(calls), expect_connected)
