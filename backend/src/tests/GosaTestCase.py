# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import mock, TestCase
from gosa.common.components import PluginRegistry

class GosaTestCase(TestCase):

    def setUp(self):
        self.registry = PluginRegistry()

    def tearDown(self):
        PluginRegistry.getInstance('HTTPService').srv.stop()
        self.registry.shutdown()
