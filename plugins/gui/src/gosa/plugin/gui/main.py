import os
import tornado.web
import pkg_resources
from gosa.common import Environment


class GuiPlugin(tornado.web.StaticFileHandler):

    def initialize(self):
        env = Environment.getInstance()
        path = None
        default = "index.html"

        if env.config.get("gui.debug", "false") == "true":
            path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                '..', '..', '..', '..', 'frontend')
            default = "gosa/source/index.html"
        else:
            path = pkg_resources.resource_filename("gosa.plugin.gui", "build")

        super(GuiPlugin, self).initialize(path, default)
