# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import TestCase
import pytest
import sys

from gosa.backend.objects.index import ObjectInfoIndex
from gosa.common import Environment
from gosa.common.components import PluginRegistry
from contextlib import contextmanager

slow = pytest.mark.skipif(
    not pytest.config.getoption("--runslow"),
    reason="need --runslow option to run"
)

@contextmanager
def gosaContext():
    try:
        yield initGosa()
    finally:
        deinitGosa()


def initGosa():
    print("skipped")
    # oreg = ObjectRegistry.getInstance()  # @UnusedVariable
    # pr = PluginRegistry()  # @UnusedVariable
    # cr = PluginRegistry.getInstance("CommandRegistry") # @UnusedVariable
    # index = PluginRegistry.getInstance("ObjectIndex")
    #
    # res = index.search({'dn': 'cn=System Administrator,ou=people,dc=example,dc=de'}, {'dn': 1})
    # print(res)
    # if len(res) > 0:
    #     sys.exit(1)


def deinitGosa():
    print("skipped")
    # PluginRegistry.getInstance('HTTPService').srv.stop()
    # PluginRegistry.shutdown()

class GosaTestCase(TestCase):

    def setUp(self):
        initGosa()

    def tearDown(self):
        deinitGosa()
