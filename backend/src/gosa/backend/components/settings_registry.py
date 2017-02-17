# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import logging
import pkg_resources
from zope.interface import implementer

from gosa.backend.exceptions import ACLException
from gosa.common import Environment
from gosa.common.error import GosaErrorHandler as C
from gosa.common.components import Plugin, PluginRegistry
from gosa.common.components.command import Command
from gosa.common.handler import IInterfaceHandler
from gosa.common.utils import N_

# Register the errors handled  by us
C.register_codes(dict(
    NO_SETTINGS_HANDLER_FOUND=N_("No settings handler found for path '%(path)s'")
))


@implementer(IInterfaceHandler)
class SettingsRegistry(Plugin):
    _priority_ = 0
    _target_ = "settings"
    __handlers = {}
    _acl = None

    def __init__(self):
        self.env = Environment.getInstance()
        self.__log = logging.getLogger(__name__)

    def serve(self):
        self._acl = PluginRegistry.getInstance("ACLResolver")
        # load registered handlers
        for entry in pkg_resources.iter_entry_points("gosa.settings_handler"):
            module = entry.load()
            self.register_handler(entry.name, module())

    def stop(self):
        # called from PluginRegistry.shutdown()
        for handler in self.__handlers.values():
            if getattr(handler, "stop"):
                handler.stop()

    def register_handler(self, path, handler):
        self.__handlers[path] = handler

    def get_handler(self, path):
        return self.__handlers[path]

    def __get_path_infos(self, path):
        if path in self.__handlers:
            return self.__handlers[path], None, path

        # find handler
        parts = path.split(".")
        param = parts.pop()

        while ".".join(parts) not in self.__handlers and len(parts) > 0:
            param = "%s.%s" % (parts.pop(), param)

        if len(parts) == 0:
            raise SettingsException(C.make_error("NO_SETTINGS_HANDLER_FOUND", path=path))

        path = ".".join(parts)
        return self.__handlers[path], param, path

    @Command(needsUser=True, __help__=N_("Change setting value"))
    def changeSetting(self, user, path, value):

        topic = "%s.settings.%s" % (self.env.domain, path)
        if not self._acl.check(user, topic, "w"):
            self.__log.debug("user '%s' has insufficient permissions to change setting in path %s" % (user, path))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic))

        handler, param, handler_path = self.__get_path_infos(path)
        handler.set(param, value)

    @Command(needsUser=True, __help__=N_("Get setting value"))
    def getSetting(self, user, path):

        topic = "%s.settings.%s" % (self.env.domain, path)
        if not self._acl.check(user, topic, "r"):
            self.__log.debug("user '%s' has insufficient permissions to read setting in path %s" % (user, path))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic))

        handler, param, handler_path = self.__get_path_infos(path)
        return handler.get(param)

    @Command(needsUser=True, __help__=N_("Returns information about the allowed settings in a path"))
    def getItemInfos(self, user, path):
        if path not in self.__handlers:
            self.__log.debug("no registered settings handler found for path %s", path)
            return {}
        handler = self.__handlers[path]
        return self.__filter_items(user, path, handler.get_item_infos())

    @Command(needsUser=True, __help__=N_("Returns information about the registered setting handlers"))
    def getSettingHandlers(self, user):
        res = {}
        for handler_path, handler in self.__handlers.items():
            handler_items = self.__filter_items(user, handler_path, handler.get_item_infos())
            if len(handler_items) > 0:
                res[handler_path] = {
                    "config": handler.get_config(),
                    "items": handler_items
                }

        return res

    def __filter_items(self, user, path, all_items):
        items = {}
        # filter out items the user cannot access
        for item_path in all_items:
            topic = "%s.settings.%s.%s" % (self.env.domain, path, item_path)
            if self._acl.check(user, topic, "r"):
                items[item_path] = all_items[item_path]
        return items


class SettingsHandler(object):
    """
    Handles config file settings
    """
    def __init__(self):
        self.config = Environment.getInstance().config

    def stop(self):
        self.config.save()

    def set(self, path, value):
        self.config.set(path, value)

    def get(self, path):
        return self.config.get(path)

    def has(self, path):
        parts = path.split(".")
        return self.config.has_section(parts[0]) and self.config.has_option(parts[0], parts[1])

    def get_config(self):
        return {}

    def get_item_infos(self):
        """
        Returns all configurable items including information about type etc.
        :return dict:
        """
        infos = {
            "backend.index": {
                "type": "boolean"
            },
            "gui.debug": {
                "type": "boolean"
            },
            "logger_gosa.level": {
                "type": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            }
        }

        # populate values
        for path in infos:
            infos[path]['value'] = self.get(path)

        return infos


class SettingsException(Exception):
    pass