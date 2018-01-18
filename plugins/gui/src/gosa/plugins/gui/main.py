import os
import pkg_resources
from tornado import gen

from gosa.common.components import PluginRegistry
from zope.interface import implementer

from gosa.common import Environment
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.gjson import loads
from gosa.common.handler import IInterfaceHandler
from gosa.common.hsts_request_handler import HSTSStaticFileHandler
from gosa.common.utils import N_

frontend_path = pkg_resources.resource_filename("gosa.plugins.gui", "data/web")


class GuiPlugin(HSTSStaticFileHandler):
    """ Static route that serves the GUI files """

    def initialize(self):
        env = Environment.getInstance()
        default = PluginRegistry.getInstance('HTTPService').get_gui_uri()[1]
        path = frontend_path

        if env.config.get("gui.debug", "false") == "true":  # pragma: nocover
            path = os.path.realpath(
                os.path.join(
                    pkg_resources.resource_filename("gosa.plugins.gui", "data"), '..', '..', '..', '..', '..', 'frontend'
                )
            )
        super(GuiPlugin, self).initialize(path, default)


class WidgetsProvider(HSTSStaticFileHandler):
    """ Static route that serves dashboard widgets (uploaded and builtin) """

    def initialize(self):
        super(WidgetsProvider, self).initialize(Environment.getInstance().config.get("gui.widget-path", default="/var/lib/gosa/widgets"))

    @gen.coroutine
    def get(self, path, include_body=True):
        namespace = path.split("/")[0]
        if not os.path.exists(os.path.join(self.root, namespace)):
            # try buildin widgets path
            if os.path.exists(os.path.join(pkg_resources.resource_filename("gosa.plugins.gui", "data/widgets"), namespace)):
                self.root = pkg_resources.resource_filename("gosa.plugins.gui", "data/widgets")

        super(WidgetsProvider, self).get(path, include_body)


@implementer(IInterfaceHandler)
class RpcPlugin(Plugin):
    _target_ = 'gui'
    _priority_ = 80

    def __init__(self):
        self.env = Environment.getInstance()
        self.buildin_widgets = self.__load_widgets(pkg_resources.resource_filename("gosa.plugins.gui", "data/widgets"))
        self.upload_path = self.env.config.get("gui.widget-path", default="/var/lib/gosa/widgets")
        if not os.path.exists(self.upload_path):
            os.makedirs(self.upload_path)

    def __load_widgets(self, path):
        widgets = []
        for root, dirs, files in os.walk(path):
            for d in dirs:
                manifest_path = os.path.join(root, d, "Manifest.json")
                if os.path.exists(manifest_path):
                    with open(manifest_path) as f:
                        plugin_data = loads(f.read())
                        widgets.append(plugin_data)
        return widgets

    @Command(__help__=N_("Returns manifest informations from all uploaded dashboard widgets."))
    def getDashboardWidgets(self):
        return self.buildin_widgets + self.__load_widgets(self.upload_path)
