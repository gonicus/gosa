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
from gosa.plugin.gui.main import GuiPlugin, PluginRegistry
import os


class GuiPluginTestCase(AsyncHTTPTestCase):

    def setUp(self):
        self.old_env = dict(os.environ)
        os.environ.update({"GOSA_CONFIG_DIR": os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "test.conf")})
        super(GuiPluginTestCase, self).setUp()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.old_env)
        super(GuiPluginTestCase, self).tearDown()

    def get_app(self):
        return Application([('/(?P<path>.*)?', GuiPlugin)])

    @mock.patch.object(PluginRegistry, 'getInstance')
    def test_get(self, mocked_http):
        mocked_http.return_value.get_gui_uri.return_value = (None, "gosa/source/index.html")

        response = self.fetch("/gosa/source/index.html")
        assert response.code == 200
