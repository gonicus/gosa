# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import os
import shutil

import logging
import pkg_resources
from zope.interface import implementer

from gosa.backend.exceptions import ACLException
from gosa.backend.routes.sse.main import SseHandler
from gosa.common.event import EventMaker
from gosa.common import Environment
from gosa.common.error import GosaErrorHandler as C
from gosa.common.components import Plugin, PluginRegistry
from gosa.common.components.command import Command
from gosa.common.handler import IInterfaceHandler
from gosa.common.utils import N_
from gosa.backend.components.workflow import Workflow, WorkflowException
from lxml import objectify, etree
from pkg_resources import resource_filename

# Register the errors handled  by us
C.register_codes(dict(
    NO_SETTINGS_HANDLER_FOUND=N_("No settings handler found for path '%(path)s'")
))


@implementer(IInterfaceHandler)
class SettingsRegistry(Plugin):
    _priority_ = 0
    _target_ = "settings"
    __handlers = {}

    def __init__(self):
        self.env = Environment.getInstance()
        self.__log = logging.getLogger(__name__)

    def serve(self):
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

    @Command(needsUser=True, __help__=N_("Change setting value"))
    def changeSetting(self, user, path, value):

        topic = "%s.settings.%s" % (self.env.domain, path)
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "w"):
            self.__log.debug("user '%s' has insufficient permissions to change setting in path %s" % (user, path))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic))

        # find handler
        parts = path.split(".")
        param = parts.pop()

        while ".".join(parts) not in self.__handlers:
            param = "%s.%s" % (parts.pop(), param)

        if len(parts) == 0:
            raise SettingsException(C.make_error("NO_SETTINGS_HANDLER_FOUND", path=path))

        handler = self.__handlers[".".join(parts)]
        handler.set(param, value)

    @Command(needsUser=True, __help__=N_("Get setting value"))
    def getSetting(self, user, path):

        topic = "%s.settings.%s" % (self.env.domain, path)
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "e"):
            self.__log.debug("user '%s' has insufficient permissions to read setting in path %s" % (user, path))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic))

        # find handler
        parts = path.split(".")
        param = parts.pop()

        while ".".join(parts) not in self.__handlers:
            param = "%s.%s" % (parts.pop(), param)

        if len(parts) == 0:
            raise SettingsException(C.make_error("NO_SETTINGS_HANDLER_FOUND", path=path))

        handler = self.__handlers[".".join(parts)]
        return handler.get(param)


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


class SettingsException(Exception):
    pass