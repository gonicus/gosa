# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import mock
from gosa.common.gjson import loads
from gosa.backend.command import CommandRegistry
from tornado.web import Application
from gosa.backend.routes.sse.main import SseHandler
from gosa.backend.components.jsonrpc_service import JsonRpcHandler
from tests.RemoteTestCase import RemoteTestCase
from tests.GosaTestCase import slow


@mock.patch("gosa.backend.command.PluginRegistry.getInstance")
class SseHandlerTestCase(RemoteTestCase):
    registry = None
    last_data = ""
    last_id = None
    last_event = None
    check_data = {}
    check_event = None

    def get_app(self):
        return Application([('/rpc', JsonRpcHandler), ('/events', SseHandler)], cookie_secret='TecloigJink4', xsrf_cookies=True)

    def send_event(self, user, data):
        if self.registry is None:
            self.registry = CommandRegistry()

        self.registry.sendEvent(user, data)

    def handle_message(self, msg):
        message_end = msg[-2:] == b'\n\n'
        for line in msg.strip().splitlines():
            (field, value) = line.decode().split(":", 1)
            field = field.strip()
            if field == "data":
                self.last_data += value.strip()
            if field == "id":
                self.last_id = value.strip()
            if field == "event":
                self.last_event = value.strip()
                assert self.last_event == self.check_event

        if message_end:
            data = loads(self.last_data)
            for key in self.check_data:
                assert key in data
                assert data[key] == self.check_data[key]

            self.last_data = ""
            self.stop()

    @slow
    def test_subscribe(self, mocked_resolver):
        mocked_resolver.return_value.check.return_value = True

        self.login()
        self.fetch_async(self.get_url('/events'), streaming_callback=self.handle_message)
        # post something
        self.check_data = {
            "body": "test",
            "title": "System notification"
        }
        self.check_event = "notification"
        self.io_loop.call_later(1, lambda: self.send_event('admin', '<Event xmlns="http://www.gonicus.de/Events"><Notification><Target>admin</Target><Body>test</Body></Notification></Event>'))
        self.wait()

    @slow
    def test_missed_events(self, mocked_resolver):
        mocked_resolver.return_value.check.return_value = True

        self.login()
        # initial connection
        future = self.fetch_async(self.get_url('/events'), streaming_callback=self.handle_message)
        self.check_data = {
            "body": "test",
            "title": "System notification"
        }
        self.check_event = "notification"
        self.io_loop.call_later(1, lambda: self.send_event('admin', '<Event xmlns="http://www.gonicus.de/Events"><Notification><Target>admin</Target><Body>test</Body></Notification></Event>'))
        self.wait()
        del future

        self.check_data = {
            "body": "deferred test",
            "title": "System notification"
        }
        self.send_event('admin', '<Event xmlns="http://www.gonicus.de/Events"><Notification><Target>admin</Target><Body>deferred test</Body></Notification></Event>')

        self.fetch_async(self.get_url('/events'), streaming_callback=self.handle_message,
                         headers={'Last-Event-ID': self.last_id})
        self.wait()

    @slow
    def test_notification(self, mocked_resolver):
        mocked_resolver.return_value.check.return_value = True

        self.login()
        self.fetch_async(self.get_url('/events'), streaming_callback=self.handle_message)

        self.check_data = {
            "body": "test",
            "title": "System notification"
        }
        self.check_event = "notification"
        self.io_loop.call_later(1, lambda: self.send_event('admin', '<Event xmlns="http://www.gonicus.de/Events"><Notification><Target>admin</Target><Body>test</Body></Notification></Event>'))
        self.wait()