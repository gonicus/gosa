# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from lxml import etree

from lxml import objectify
from unittest import mock

import datetime
from gosa.common.gjson import loads
from gosa.backend.command import CommandRegistry
from tornado.web import Application
from gosa.backend.routes.sse.main import SseHandler
from gosa.backend.components.jsonrpc_service import JsonRpcHandler
from tests.RemoteTestCase import RemoteTestCase
from tests.GosaTestCase import slow
from gosa.common.event import EventMaker


class TestSseHandler(SseHandler):
    """ Inherits from SseHandler to access some protected properties """
    _cache_size = 5

    @classmethod
    def get_connections(cls):
        return SseHandler._connections

    @classmethod
    def get_channels(cls):
        return SseHandler._channels

    @classmethod
    def get_cache(cls):
        return SseHandler._cache


@mock.patch("gosa.backend.command.PluginRegistry.getInstance")
class SseHandlerTestCase(RemoteTestCase):
    registry = None
    last_data = ""
    last_id = None
    last_event = None
    check_data = {}
    check_event = None

    def get_app(self):
        return Application([('/rpc', JsonRpcHandler), ('/events', TestSseHandler)], cookie_secret='TecloigJink4', xsrf_cookies=True)

    def send_event(self, user, data):
        if self.registry is None:
            self.registry = CommandRegistry()

        self.registry.sendEvent(user, data)

    def handle_message(self, msg):
        message_end = msg[-2:] == b'\n\n'
        for line in msg.strip().splitlines():
            if line == b'ping':
                # skip the ping events
                continue
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
            print("msg id %s (%s) received" % (self.last_id, data['uuid']))
            self.stop()

    @slow
    def test_subscribe(self, mocked_resolver):
        mocked_resolver.return_value.check.return_value = True

        # not authorized
        response = self.fetch('/events')
        assert response.code == 401

        self.login()
        self.fetch_async(self.get_url('/events'), streaming_callback=self.handle_message)
        # post something
        self.check_data = {
            "uuid": "uuid",
            "changeType": "modify"
        }
        e = EventMaker()

        self.check_event = "objectChange"
        self.io_loop.call_later(1, lambda: self.send_event('admin',
                                                           e.Event(
                                                               e.ObjectChanged(
                                                                   e.UUID('uuid'),
                                                                   e.ModificationTime("20150101000000Z"),
                                                                   e.ChangeType("modify")
                                                               )
                                                           )))
        self.wait()

    @slow
    def test_missed_events(self, mocked_resolver):
        mocked_resolver.return_value.check.return_value = True

        self.login()
        # initial connection
        self.fetch_async(self.get_url('/events'), streaming_callback=self.handle_message)
        self.check_data = {
            "uuid": "test"
        }
        self.check_event = "objectChange"
        e = EventMaker()
        self.io_loop.call_later(1, lambda: self.send_event('admin',
                                                           e.Event(
                                                               e.ObjectChanged(
                                                                   e.UUID('test'),
                                                                   e.ModificationTime("20150101000000Z"),
                                                                   e.ChangeType("modify")
                                                               )
                                                           )))

        self.wait()
        for connection_id in list(TestSseHandler.get_connections()):
            connection = TestSseHandler.get_connections()[connection_id]
            connection.on_connection_close()
            del connection

        self.check_data = {
            "uuid": "deferred test"
        }
        self.send_event('admin', e.Event(
            e.ObjectChanged(
                e.UUID('deferred test'),
                e.ModificationTime("20150101000000Z"),
                e.ChangeType("modify")
            )
        ))
        self.fetch_async(self.get_url('/events'), streaming_callback=self.handle_message,
                         headers={'Last-Event-ID': self.last_id})
        # for some reason the first wait stops immediately
        self.wait()
        # so we need to wait one more tine for the message
        self.wait()

    def test_notification(self, mocked_resolver):
        e = EventMaker()
        with mock.patch("gosa.backend.routes.sse.main.SseHandler.send_message") as m_send:
            event = e.Event(
                e.Notification(
                    e.Target('admin'),
                    e.Body('Test'),
                    e.Title('Notification'),
                    e.Icon('test-icon'),
                    e.Timeout("1000")
                )
            )
            event_object = objectify.fromstring(etree.tostring(event, pretty_print=True).decode('utf-8'))
            SseHandler.notify(event_object, event_object.Notification.Target)

            m_send.assert_called_with({
                "title": "Notification",
                "body": "Test",
                "icon": "test-icon",
                "timeout": 1000
            }, topic="notification", channel="admin")

            SseHandler.notify(event_object)

            m_send.assert_called_with({
                "title": "Notification",
                "body": "Test",
                "icon": "test-icon",
                "timeout": 1000
            }, topic="notification", channel="broadcast")

    def test_objectChanged(self, mocked_resolver):
        e = EventMaker()
        mod = datetime.datetime.now().strftime("%Y%m%d%H%M%SZ")
        with mock.patch("gosa.backend.routes.sse.main.SseHandler.send_message") as m_send:
            event = e.Event(
                e.ObjectChanged(
                    e.UUID('fake_uuid'),
                    e.DN('fake_dn'),
                    e.ModificationTime(mod),
                    e.ChangeType('fake_change_type')
                )
            )
            event_object = objectify.fromstring(etree.tostring(event, pretty_print=True).decode('utf-8'))
            SseHandler.notify(event_object, "admin")

            m_send.assert_called_with({
                "uuid": "fake_uuid",
                "dn": "fake_dn",
                "lastChanged": mod,
                "changeType": "fake_change_type"
            }, topic="objectChange", channel="admin")

            SseHandler.notify(event_object)

            m_send.assert_called_with({
                "uuid": "fake_uuid",
                "dn": "fake_dn",
                "lastChanged": mod,
                "changeType": "fake_change_type"
            }, topic="objectChange", channel="broadcast")

    def test_objectCloseAnnouncement(self, mocked_resolver):
        e = EventMaker()
        with mock.patch("gosa.backend.routes.sse.main.SseHandler.send_message") as m_send:
            event = e.Event(
                e.ObjectCloseAnnouncement(
                    e.UUID('fake_uuid'),
                    e.Minutes('1'),
                    e.State('fake_state'),
                    e.SessionId('fake_session_id')
                )
            )
            event_object = objectify.fromstring(etree.tostring(event, pretty_print=True).decode('utf-8'))
            SseHandler.notify(event_object, "admin")

            m_send.assert_called_with({
                "uuid": "fake_uuid",
                "minutes": "1",
                "state": "fake_state",
            }, topic="objectCloseAnnouncement", channel="admin", session_id="fake_session_id")

            SseHandler.notify(event_object)

            m_send.assert_called_with({
                "uuid": "fake_uuid",
                "minutes": "1",
                "state": "fake_state",
            }, topic="objectCloseAnnouncement", channel="broadcast", session_id="fake_session_id")

    @mock.patch("gosa.backend.routes.sse.main.uuid.uuid4", return_value="fake_uuid")
    def test_send_message(self, mocked_resolver, m_uuid):
        # fake some connections / channels
        connections = TestSseHandler.get_connections()
        con1 = mock.MagicMock()
        con2 = mock.MagicMock()
        con3 = mock.MagicMock()
        connections['fake_connection_id1'] = con1
        connections['fake_connection_id2'] = con2
        connections['fake_connection_id3'] = con3

        channels = TestSseHandler.get_channels()
        channels['admin'] = {
            'fake_connection_id1': 'fake_session_id1',
            'fake_connection_id2': 'fake_session_id2'
        }
        channels['tester'] = {'fake_connection_id3': 'fake_session_id3'}

        # test the routing

        # broadcast to all
        TestSseHandler.send_message("Test")
        con1.on_message.assert_called_with('id: fake_uuid\ndata: Test\n\n')
        con2.on_message.assert_called_with('id: fake_uuid\ndata: Test\n\n')
        con3.on_message.assert_called_with('id: fake_uuid\ndata: Test\n\n')
        con1.reset_mock()
        con2.reset_mock()
        con3.reset_mock()

        # 'admin' to con1,con2
        TestSseHandler.send_message("Test", channel="admin")
        con1.on_message.assert_called_with('id: fake_uuid\ndata: Test\n\n')
        con2.on_message.assert_called_with('id: fake_uuid\ndata: Test\n\n')
        assert not con3.on_message.called
        con1.reset_mock()
        con2.reset_mock()

        # 'tester' to con3
        TestSseHandler.send_message("Test", channel="tester")
        con3.on_message.assert_called_with('id: fake_uuid\ndata: Test\n\n')
        assert not con1.on_message.called
        assert not con2.on_message.called
        con3.reset_mock()

        # fake_session_id1 to con1
        TestSseHandler.send_message("Test", channel="admin", session_id="fake_session_id1")
        con1.on_message.assert_called_with('id: fake_uuid\ndata: Test\n\n')
        assert not con2.on_message.called
        assert not con3.on_message.called
        con1.reset_mock()

        # 'fake_session_id2' to con2
        TestSseHandler.send_message("Test", channel="admin", session_id="fake_session_id2")
        con2.on_message.assert_called_with('id: fake_uuid\ndata: Test\n\n')
        assert not con1.on_message.called
        assert not con3.on_message.called
        con2.reset_mock()

        # check the cache size limit
        for num in range(0, 10):
            TestSseHandler.send_message("Test")
            assert len(TestSseHandler.get_cache()) <= 6
