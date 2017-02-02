import os

from gosa.common.components import PluginRegistry
from zope.interface import implementer

from gosa.common import Environment
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.gjson import loads
from gosa.common.handler import IInterfaceHandler
from gosa.common.hsts_request_handler import HSTSStaticFileHandler
from gosa.common.utils import N_

frontend_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', '..', 'frontend'))


class GuiPlugin(HSTSStaticFileHandler):

    def initialize(self):
        env = Environment.getInstance()
        default = PluginRegistry.getInstance('HTTPService').get_gui_uri()[1]
        path = frontend_path

        if env.config.get("gui.debug", "false") == "false":  # pragma: nocover
            path = os.path.join(frontend_path, 'gosa', 'build')

        super(GuiPlugin, self).initialize(path, default)


@implementer(IInterfaceHandler)
class RpcPlugin(Plugin):
    _target_ = 'gui'
    _priority_ = 80

    @Command(__help__=N_("Returns manifest informations from all uploaded dashboard widgets."))
    def getDashboardWidgets(self):
        plugins = []
        for root, dirs, files in os.walk(os.path.join(frontend_path, 'gosa', 'uploads', 'widgets')):
            for d in dirs:
                manifest_path = os.path.join(root, d, "Manifest.json")
                if os.path.exists(manifest_path):
                    with open(manifest_path) as f:
                        plugin_data = loads(f.read())
                        plugins.append(plugin_data)
        return plugins
