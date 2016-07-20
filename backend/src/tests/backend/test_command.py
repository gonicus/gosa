# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
import pytest
from gosa.backend.command import *
from gosa.common.events import ZopeEventConsumer
from tests.GosaTestCase import slow

@slow
class CommandRegistryTestCase(unittest.TestCase):

    def setUp(self):
        super(CommandRegistryTestCase, self).setUp()
        self.reg = PluginRegistry.getInstance("CommandRegistry")

    def test_getBase(self):
        assert self.reg.getBase() == "dc=example,dc=net"

    def test_getMethods(self):
        res = self.reg.getMethods()
        assert len(res) > 0
        assert 'setUserPassword' in res
        assert res['setUserPassword']['doc'] == 'Sets a new password for a user'

        # another locale
        # res = self.reg.getMethods("de")
        # print(res)
        # assert len(res) > 0
        # assert 'setUserPassword' in res
        # assert res['setUserPassword']['doc'] == 'Setzt ein neues Benutzerpasswort'

    def test_shutdown(self):
        with unittest.mock.patch.object(PluginRegistry.getInstance('HTTPService'),'stop') as m:
            assert self.reg.shutdown() is True
            assert m.called is True


    def test_dispatch(self):

        with pytest.raises(CommandNotAuthorized):
            self.reg.dispatch(None, None)

        with pytest.raises(CommandInvalid):
            self.reg.dispatch(self.reg, 'unknownCommand')

        res = self.reg.dispatch(self.reg, 'getBase')
        assert res == "dc=example,dc=net"


    def test_callNeedsUser(self):
        with pytest.raises(CommandInvalid):
            self.reg.callNeedsUser('unknownCommand')

        assert self.reg.callNeedsUser('getSessionUser') is True

    def test_sendEvent(self):
        backendChangeData = '<Event xmlns="http://www.gonicus.de/Events"><BackendChange><ChangeType>modify</ChangeType><ModificationTime>20150101000000Z</ModificationTime></BackendChange></Event>'
        data = '<Event xmlns="http://www.gonicus.de/Events"><Notification><Target>admin</Target><Body>test</Body></Notification></Event>'

        mocked_resolver = unittest.mock.MagicMock()
        mocked_resolver.check.return_value = False
        with unittest.mock.patch.dict("gosa.backend.command.PluginRegistry.modules", {'ACLResolver': mocked_resolver}),\
                unittest.mock.patch("gosa.backend.command.SseHandler.send_message") as mocked_sse:

            with pytest.raises(EventNotAuthorized):
                self.reg.sendEvent('admin', data)

            mocked_resolver.check.return_value = True

            with pytest.raises(etree.XMLSyntaxError):
                # message without content
                self.reg.sendEvent('admin', '<Event xmlns="http://www.gonicus.de/Events"><Notification></Notification></Event>')


            # add listener
            handle_event = unittest.mock.MagicMock()

            ZopeEventConsumer(type='Message', callback=handle_event.process)
            self.reg.sendEvent('admin', backendChangeData)
            assert not handle_event.process.called

            # send data as str
            self.reg.sendEvent('admin', data)
            assert handle_event.process.called
            args, kwargs = handle_event.process.call_args
            called_string = etree.tostring(args[0])
            assert called_string.decode() == data
            handle_event.reset_mock()

            # send data as bytes
            self.reg.sendEvent('admin', bytes(data, 'utf-8'))
            assert handle_event.process.called
            args, kwargs = handle_event.process.call_args
            called_string = etree.tostring(args[0])
            assert called_string.decode() == data
            handle_event.reset_mock()

            # send data as xml
            self.reg.sendEvent('admin', etree.fromstring(data))
            assert handle_event.process.called
            args, kwargs = handle_event.process.call_args
            called_string = etree.tostring(args[0])
            assert called_string.decode() == data
            handle_event.reset_mock()

            # send data with target all
            data = '<Event xmlns="http://www.gonicus.de/Events"><Notification><Target>all</Target><Body>test</Body></Notification></Event>'
            self.reg.sendEvent('admin', data)
            assert handle_event.process.called
            args, kwargs = handle_event.process.call_args
            called_string = etree.tostring(args[0])
            assert called_string.decode() == data
            args, kwargs = mocked_sse.call_args
            assert kwargs.get('channel') == "broadcast"
