# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import uuid
from unittest import TestCase, mock

import pytest
from lxml import etree

from gosa.common import Environment
from gosa.common.components import PluginRegistry
from gosa.common.components.jsonrpc_utils import BadServiceRequest
from gosa.common.event import EventMaker
from gosa.common.gjson import dumps, loads


class MQTTRPCServiceTestCase(TestCase):

    def test_clientLeave(self):
        service = PluginRegistry.getInstance("MQTTRPCService")
        e = EventMaker()
        goodbye = e.Event(e.ClientLeave(e.Id("fake_uuid")))
        data = etree.tostring(goodbye).decode('utf-8')

        with mock.patch.object(PluginRegistry.getInstance("BackendRegistry"), "unregisterBackend") as m:
            service.handle_request("%s/proxy" % Environment.getInstance().domain, data)
            m.assert_called_with("fake_uuid")

    def test_rpc(self):
        service = PluginRegistry.getInstance("MQTTRPCService")
        request_uuid = uuid.uuid4()
        topic = "%s/proxy/fake_client_id/%s" % (Environment.getInstance().domain, request_uuid)

        with mock.patch.object(PluginRegistry.getInstance('CommandRegistry'), "dispatch") as m, \
                mock.patch.object(service.mqtt, "send_message") as mq:
            m.return_value = "fake_response"
            # call with wrong json
            service.handle_request(topic, "this is no json: 'string'")
            args, kwargs = mq.call_args
            response = loads(args[0])
            assert "error" in response
            assert kwargs["topic"] == "%s/response" % topic
            assert not m.called
            mq.reset_mock()

            # call without params
            service.handle_request(topic, dumps({
                "id": "jsonrpc",
                "method": "fakeCall",
                "user": "admin"
            }))
            args, kwargs = mq.call_args
            response = loads(args[0])
            assert "error" in response
            assert kwargs["topic"] == "%s/response" % topic
            assert not m.called

            # call with empty params
            service.handle_request(topic, dumps({
                "id": "jsonrpc",
                "method": "fakeCall",
                "user": "admin",
                "session_id": "fake_session_id",
                "params": []
            }))
            m.assert_called_with("admin", "fake_session_id", "fakeCall")
            args, kwargs = mq.call_args
            response = loads(args[0])
            assert "result" in response
            assert response["result"] == "fake_response"
            assert kwargs["topic"] == "%s/response" % topic
            mq.reset_mock()
            m.reset_mock()

            service.handle_request(topic, dumps({
                "id": "jsonrpc",
                "method": "fakeCall",
                "user": "admin",
                "params": ["param1", "param2"]
            }))
            m.assert_called_with("admin", None, "fakeCall", "param1", "param2")
            args, kwargs = mq.call_args
            response = loads(args[0])
            assert "result" in response
            assert response["result"] == "fake_response"
            assert kwargs["topic"] == "%s/response" % topic

            mq.reset_mock()
            m.reset_mock()

            # call without user (client id taken as user)
            service.handle_request(topic, dumps({
                "id": "jsonrpc",
                "method": "fakeCall",
                "params": []
            }))
            m.assert_called_with("fake_client_id", None, "fakeCall")
            args, kwargs = mq.call_args
            response = loads(args[0])
            assert "result" in response
            assert response["result"] == "fake_response"
            assert kwargs["topic"] == "%s/response" % topic

