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
import os
from gosa.common import Environment
from gosa.common.components import PluginRegistry, ObjectRegistry
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
    Environment.reset()
    Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test.conf")
    Environment.noargs = True
    oreg = ObjectRegistry.getInstance()  # @UnusedVariable
    pr = PluginRegistry()  # @UnusedVariable
    cr = PluginRegistry.getInstance("CommandRegistry") # @UnusedVariable


def deinitGosa():
    PluginRegistry.getInstance('HTTPService').srv.stop()
    PluginRegistry.shutdown()

class GosaTestCase(TestCase):

    def setUp(self):
        initGosa()

    def tearDown(self):
        deinitGosa()
