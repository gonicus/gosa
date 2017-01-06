import os
from gosa.common import Environment
from gosa.common.hsts_request_handler import HSTSStaticFileHandler
from gosa.plugin.gui import frontend_path


class GuiPlugin(HSTSStaticFileHandler):

    def initialize(self):
        env = Environment.getInstance()
        default = "index.html"
        path = frontend_path

        if env.config.get("gui.debug", "false") == "true":  # pragma: nocover
            default = "gosa/source/index.html"
        else:
            path = os.path.join(frontend_path, 'gosa', 'build')

        super(GuiPlugin, self).initialize(path, default)
