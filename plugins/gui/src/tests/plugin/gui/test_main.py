# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application
from unittest import mock
from gosa.plugins.gui.main import GuiPlugin, PluginRegistry
import os


class GuiPluginTestCase(AsyncHTTPTestCase):

    def get_app(self):
        return Application([('/(?P<path>.*)?', GuiPlugin)])

    @mock.patch.object(PluginRegistry, 'getInstance')
    def test_get(self, mocked_http):
        mocked_http.return_value.get_gui_uri.return_value = (None, "gosa/source/index.html")

        response = self.fetch("/gosa/source/index.html")
        assert response.code == 200
