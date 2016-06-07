import pkg_resources
import os
from flask import send_from_directory
from flask.views import MethodView

class GuiPlugin(MethodView):

    def __init__(self):
        #self.root = pkg_resources.resource_filename('gosa.plugin.gui', 'frontend/build')
        # TODO: hardcoded path should be replaced later
        self.root = os.path.join(os.getcwd(), 'plugins', 'gui', 'frontend', 'gosa', 'build')

    def get(self, path):
        return send_from_directory(self.root, path)