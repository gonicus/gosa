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
from gosa.plugin.gui.main import GuiPlugin


class GuiPluginTestCase(AsyncHTTPTestCase):

    def get_app(self):
        return Application([('/(?P<path>.*)?', GuiPlugin)])

    def test_get(self):
        response = self.fetch("/index.html")
        assert response.code == 200
