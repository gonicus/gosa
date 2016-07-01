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
from tests.GosaTestCase import GosaTestCase

class CommandRegistryTestCase(GosaTestCase):

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