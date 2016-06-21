from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application
from gosa.plugin.gui.main import GuiPlugin

class GuiPluginTestCase(AsyncHTTPTestCase):
    def get_app(self):
        return Application([('/(?P<path>.*)?', GuiPlugin)])

    def test_get(self):
        response = self.fetch("/")
        assert response.code == 200