import os
import tornado.web
import pkg_resources
from gosa.common import Environment
from gosa.common.hsts_request_handler import HSTSStaticFileHandler


class GuiPlugin(HSTSStaticFileHandler):

    def initialize(self):
        env = Environment.getInstance()
        path = None
        default = "index.html"

        if env.config.get("gui.debug", "false") == "true":  # pragma: nocover
            path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                    '..', '..', '..', '..', 'frontend'))
            default = "gosa/source/index.html"
        else:
            path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                    '..', '..', '..', '..', 'frontend', 'gosa', 'build'))
        super(GuiPlugin, self).initialize(path, default)
