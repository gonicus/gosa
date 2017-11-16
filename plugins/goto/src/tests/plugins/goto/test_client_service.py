# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import pytest
from tornado.concurrent import Future
from tornado.testing import AsyncTestCase, gen_test
from unittest import mock
from gosa.plugins.goto.client_service import *


class MQTTHandlerMock(mock.MagicMock):
    callback = None

    def set_subscription_callback(self, cb):
        self.callback = cb

    def simulate_message(self, topic, message):
        self.callback(topic, message)


class GotoClientServiceTestCase(AsyncTestCase):

    def setUp(self):
        super(GotoClientServiceTestCase, self).setUp()
        self.service = ClientService()
        # use the mocked handler instead of the real one
        self.service.mqtt = MQTTHandlerMock()
        self.service.serve()

    def __announce_client(self):
        e = EventMaker()
        netinfo = []
        more = []
        netinfo.append(
            e.NetworkDevice(
                e.Name("eth0"),
                e.IPAddress("127.0.0.1"),
                e.IPv6Address("::1/128"),
                e.MAC("00:00:00:00:01"),
                e.Netmask("255.255.255.0"),
                e.Broadcast("127.0.0.255")))
        more.append(e.NetworkInformation(*netinfo))

        info = e.Event(
            e.ClientAnnounce(
                e.Id("fake_client_uuid"),
                e.Name("Testclient"),
                *more))

        self.service.mqtt.simulate_message("net.example/client/fake_client_uuid", etree.tostring(info))

    def __announce_client_caps(self):
        e = EventMaker()
        # Assemble capabilities
        more = []
        caps = []
        caps.append(
            e.ClientMethod(
                e.Name("fakeCommand"),
                e.Path("path"),
                e.Signature("signature"),
                e.Documentation("This is a fake command for testing purpose")))
        more.append(e.ClientCapabilities(*caps))

        info = e.Event(
            e.ClientSignature(
                e.Id('fake_client_uuid'),
                e.Name('Testclient'),
                *more))
        self.service.mqtt.simulate_message("net.example/client/fake_client_uuid", etree.tostring(info))

    def __set_client_offline(self, uuid):
        utcnow = datetime.datetime.utcnow() - datetime.timedelta(seconds=1500)
        e = EventMaker()
        # set client offline
        with mock.patch("gosa.plugins.goto.client_service.datetime.datetime") as m:
            m.utcnow.return_value = utcnow
            # send a client ping to store the faked current time
            ping = e.Event(e.ClientPing(e.Id(uuid)))
            self.service.mqtt.simulate_message("net.example/client/%s" % uuid, etree.tostring(ping))

        # run garbage collection
        self.service._ClientService__gc()

    @mock.patch("gosa.plugins.goto.client_service.ClientService.systemSetStatus")
    @mock.patch("gosa.plugins.goto.client_service.ClientService.systemGetStatus", return_value="")
    def test_clients(self, mocked_get_status, mocked_set_status):
        assert self.service.getClients() == {}

        # announce fake client via MQTT
        self.__announce_client()

        clients = self.service.getClients()
        assert len(clients) == 1
        assert "fake_client_uuid" in clients
        assert clients["fake_client_uuid"]["name"] == "Testclient"

        net = self.service.getClientNetInfo('fake_client_uuid')
        assert "eth0" in net
        assert net["eth0"]['IPAddress'] == "127.0.0.1"

        assert self.service.getClientNetInfo('unknown_client_uuid') == []

        assert self.service.getClientMethods('unknown_client_uuid') == []
        assert self.service.getClientMethods('fake_client_uuid') == {}

        self.__announce_client_caps()
        methods = self.service.getClientMethods('fake_client_uuid')
        assert 'fakeCommand' in methods

        self.__set_client_offline('fake_client_uuid')
        assert self.service.getClientMethods('fake_client_uuid') == []

        # disconnect client
        e = EventMaker()
        offline = e.Event(e.ClientLeave(
            e.Id('fake_client_uuid')
        ))
        self.service.mqtt.simulate_message("net.example/client/fake_client_uuid", etree.tostring(offline))
        assert self.service.getClientMethods('fake_client_uuid') == []

    @mock.patch("gosa.plugins.goto.client_service.ClientService.systemSetStatus")
    @mock.patch("gosa.plugins.goto.client_service.ClientService.systemGetStatus", return_value="")
    @gen_test
    def test_clientDispatch(self, mocked_get_status, mocked_set_status):
        # announce fake client via MQTT
        self.__announce_client()
        self.__announce_client_caps()

        with pytest.raises(JSONRPCException):
            yield self.service.clientDispatch('unknown_client', 'fakeCommand')

        with pytest.raises(JSONRPCException):
            yield self.service.clientDispatch('fake_client_uuid', 'unknown_command')

        with mock.patch("gosa.plugins.goto.client_service.MQTTServiceProxy") as m:
            future = Future()
            future.set_result("result")
            m.return_value.fakeCommand.return_value = future
            res = yield self.service.clientDispatch('fake_client_uuid', 'fakeCommand')
            assert res == "result"

        self.__set_client_offline('fake_client_uuid')
        with pytest.raises(JSONRPCException):
            yield self.service.clientDispatch('fake_client_uuid', 'fakeCommand')


    @mock.patch("gosa.plugins.goto.client_service.ClientService.systemSetStatus")
    @mock.patch("gosa.plugins.goto.client_service.ClientService.systemGetStatus", return_value="")
    def test_users(self, mocked_get_status, mocked_set_status):
        # setup users
        self.__announce_client()
        self.__announce_client_caps()

        # setup session
        e = EventMaker()
        info = e.Event(
            e.UserSession(
                e.Id('fake_client_uuid'),
                e.User(e.Name('tester'))))

        self.service.mqtt.simulate_message("net.example/client/fake_client_uuid", etree.tostring(info))

        assert self.service.getUserSessions()[0] == 'fake_client_uuid'

        assert self.service.getUserSessions("unknown_client_uuid") == []
        assert self.service.getUserSessions("fake_client_uuid")[0] == 'tester'

        assert self.service.getUserClients("tester") == ['fake_client_uuid']
        assert self.service.getUserClients("unknown_user") == []

        # notify user
        with mock.patch.object(self.service, "clientDispatch") as m:
            self.service.notifyUser('unknown_user', 'Title', 'Message')
            assert not m.called

            self.service.notifyUser('tester', 'Title', 'Message')
            m.assert_called_with('fake_client_uuid', 'notify', 'tester', 'Title', 'Message', 10, 'dialog-information')
            m.reset_mock()

            self.service.notifyUser('tester', 'Title', 'Message', icon=None)
            m.assert_called_with('fake_client_uuid', 'notify', 'tester', 'Title', 'Message', 10, '_no_icon_')

            m.reset_mock()
            m.side_effect = Exception("test")
            self.service.notifyUser('tester', 'Title', 'Message')
            m.side_effect = None

            with mock.patch("gosa.plugins.goto.client_service.JsonRpcHandler.user_sessions_available", return_value=True):
                self.service.notifyUser('tester', 'Title', 'Message')
                assert self.service.mqtt.send_event.called

            m.reset_mock()
            self.service.mqtt.send_event.reset_mock()

            # all users
            self.service.notifyUser(None, 'Title', 'Message')
            m.assert_called_with('fake_client_uuid', 'notify_all', 'Title', 'Message', 10, 'dialog-information')

            with mock.patch("gosa.plugins.goto.client_service.JsonRpcHandler.user_sessions_available", return_value=True):
                self.service.notifyUser(None, 'Title', 'Message')
                assert self.service.mqtt.send_event.called

            m.reset_mock()
            m.side_effect = Exception("test")
            self.service.notifyUser(None, 'Title', 'Message')

        # remove the user
        info = e.Event(
            e.UserSession(
                e.Id('fake_client_uuid'), e.User()))
        self.service.mqtt.simulate_message("net.example/client/fake_client_uuid", etree.tostring(info))
        assert len(self.service.getUserSessions("fake_client_uuid")) == 0

    @mock.patch("gosa.plugins.goto.client_service.ObjectProxy")
    def test_systemGetStatus(self, mocked_proxy):
        mocked_proxy.return_value.deviceStatus = "O"
        with mock.patch("gosa.plugins.goto.client_service.PluginRegistry.getInstance") as mocked_index:
            mocked_index.return_value.search.return_value = []

            with pytest.raises(ValueError):
                self.service.systemGetStatus('some_uuid')

            mocked_index.return_value.search.return_value = [{'_uuid': ["some_uuid"]}]

            assert self.service.systemGetStatus('some_uuid') == "O"

    @mock.patch("gosa.plugins.goto.client_service.ObjectProxy")
    def test_systemSetStatus(self, mocked_proxy):
        with mock.patch("gosa.plugins.goto.client_service.PluginRegistry.getInstance") as mocked_index:
            mocked_index.return_value.search.return_value = []

            with pytest.raises(ValueError):
                self.service.systemSetStatus('some_uuid', "+O")

            mocked_index.return_value.search.return_value = [{'_uuid': 'some_uuid'}]
            self.service.systemSetStatus('some_uuid', "-O")
            mocked_proxy.return_value.system_Online is False

            with pytest.raises(ValueError):
                self.service.systemSetStatus('some_uuid', "+X")

            self.service.systemSetStatus('some_uuid', "+U")
            mocked_proxy.return_value.status_UpdateInProgress is True

            self.service.systemSetStatus('some_uuid', "-U")
            mocked_proxy.return_value.status_UpdateInProgress is False

    @mock.patch("gosa.plugins.goto.client_service.ObjectProxy")
    def test_joinClient(self, mocked_proxy):

        with mock.patch("gosa.plugins.goto.client_service.PluginRegistry.getInstance") as mocked_reg:
            mocked_index = mocked_reg.return_value
            with pytest.raises(ValueError):
                self.service.joinClient('tester', 'wrong_uuid', '00:00:00:00:00:01')

            # device exists
            # mocked_index.search.return_value = [1]
            # with pytest.raises(GOtoException):
            #     self.service.joinClient('tester', 'fff0c8ad-d26b-4b6d-8e8e-75e054614dd9', '00:00:00:00:00:01')

            # user not unique
            mocked_index.search.side_effect = [[], [1, 2]]
            with pytest.raises(GOtoException):
                self.service.joinClient('tester', 'fff0c8ad-d26b-4b6d-8e8e-75e054614dd9', '00:00:00:00:00:01')

            mocked_index.search.side_effect = [[], [{'dn': 'fake-manager-dn'}]]
            self.service.joinClient('tester', 'fff0c8ad-d26b-4b6d-8e8e-75e054614dd9', '00:00:00:00:00:01')
            assert mocked_proxy.return_value.commit.called

            mocked_proxy.reset_mock()
            mocked_index.search.side_effect = None

            # with info
            with pytest.raises(ValueError):
                # wrong value type
                self.service.joinClient('tester', 'fff0c8ad-d26b-4b6d-8e8e-75e054614dd9', '00:00:00:00:00:01', info={'ou': '&/(&'})

            with pytest.raises(ValueError):
                # wrong deviceType
                self.service.joinClient('tester', 'fff0c8ad-d26b-4b6d-8e8e-75e054614dd9', '00:00:00:00:00:01', info={'ou': 'devices',
                                                                                                                     'deviceType': 'unknown'})

            mocked_index.search.side_effect = [[], [], [{'dn': 'fake-manager-dn'}]]
            with pytest.raises(ValueError):
                # wrong owner
                self.service.joinClient('tester', 'fff0c8ad-d26b-4b6d-8e8e-75e054614dd9', '00:00:00:00:00:01', info={'ou': 'devices',
                                                                                                                     'deviceType': 'terminal',
                                                                                                                     'owner': 'tester'})
            mocked_index.search.side_effect = [['tester-dn'], [], [{'dn': 'fake-manager-dn'}]]
            self.service.joinClient('tester', 'fff0c8ad-d26b-4b6d-8e8e-75e054614dd9', '00:00:00:00:00:01', info={'ou': 'devices',
                                                                                                                 'deviceType': 'terminal',
                                                                                                                 'owner': 'tester'})
            assert mocked_proxy.return_value.commit.called
            assert mocked_proxy.return_value.owner == "tester"
            assert mocked_proxy.return_value.deviceType == "terminal"
            assert mocked_proxy.return_value.ou == "devices"

    def test_listeners(self):
        callback1 = mock.MagicMock()
        callback2 = mock.MagicMock()
        self.service.register_listener('testMethod1', callback1)
        self.service.register_listener('testMethod2', callback2)

        self.service.unregister_listener('testMethod3', callback1)
        self.service.unregister_listener('testMethod2', callback1)
        self.service.unregister_listener('testMethod2', callback2)

        self.service.notify_listeners("id1", "testMethod1", "state1")
        self.service.notify_listeners("id2", "testMethod2", "state2")

        callback1.assert_called_with("id1", "testMethod1", "state1")
        assert not callback2.called

    def test_eventProcessor(self):
        with mock.patch.object(self.service.log, "debug") as m:
            self.service.mqtt.simulate_message("net.example/client/fake_client_uuid", "{}")
            assert m.called

        e = EventMaker()
        event = e.Event(e.UnknownEvent())
        with mock.patch.object(self.service.log, "error") as m:
            self.service.mqtt.simulate_message("net.example/client/fake_client_uuid", etree.tostring(event))
            assert m.called
