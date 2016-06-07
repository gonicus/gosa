import pkg_resources
from flask import send_from_directory
from flask.views import MethodView

class GuiPlugin(MethodView):

    def __init__(self):
        self.root = pkg_resources.resource_filename('gosa.plugin.gui', 'frontend/build')

    def get(self, path):
        return send_from_directory(self.root, path)