# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import pytest
from unittest import TestCase, mock
from gosa.client.command import *
from gosa.common.components import Command


class TestModule(object):
    @Command()
    def test_func1(self, param):
        """ Documentation """
        return True


class TestModule2(object):
    @Command()
    def undocumented_func(self):
        return True


class ClientCommandTestCase(TestCase):

    def test_undocumented(self):
        with mock.patch.dict("gosa.client.command.PluginRegistry.modules", {'TestModule2': TestModule2}),\
                pytest.raises(Exception):
            ClientCommandRegistry()

    def test_commands(self):
        with mock.patch.dict("gosa.client.command.PluginRegistry.modules", {'TestModule': TestModule}):
            reg = ClientCommandRegistry()
            reg.register('test_func2', 'path2', [], 'signature2', 'documentation2')

            res = reg.getMethods()
            assert 'test_func1' in res
            assert 'test_func2' in res
            reg.unregister('test_func2')
            assert 'test_func1' in res
            assert 'test_func2' not in res

            with pytest.raises(CommandInvalid):
                reg.dispatch('test_func2')

        with mock.patch.dict("gosa.client.command.PluginRegistry.modules", {'TestModule': TestModule()}):
            assert reg.dispatch('test_func1', 'test') is True
