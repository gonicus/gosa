# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import os
import logging
from inspect import isclass
from lxml import etree
from pkg_resources import resource_filename, resource_listdir, iter_entry_points, resource_isdir #@UnresolvedImport
from gosa.common.handler import IInterfaceHandler
from gosa.common import Environment
from io import StringIO


class PluginRegistry(object):
    """
    Plugin registry class. The registry holds plugin instances and
    provides overall functionality like "serve" and "shutdown".

    =============== ============
    Parameter       Description
    =============== ============
    component       What setuptools entrypoint to use when looking for :class:`gosa.common.components.plugin.Plugin`.
    =============== ============
    """
    modules = {}
    handlers = {}
    evreg = {}

    def __init__(self, component="gosa.plugin"):
        env = Environment.getInstance()
        self.env = env
        self.log = logging.getLogger(__name__)
        self.log.debug("inizializing plugin registry")

        # Get module from setuptools
        for entry in iter_entry_points(component):
            module = entry.load()
            self.log.info("module %s included" % module.__name__)
            PluginRegistry.modules[module.__name__] = module

            # Save interface handlers
            # pylint: disable=E1101
            if IInterfaceHandler.implementedBy(module):
                self.log.debug("registering handler module %s" % module.__name__)
                PluginRegistry.handlers[module.__name__] = module

        # Initialize component handlers
        for handler, clazz in PluginRegistry.handlers.items():
             PluginRegistry.handlers[handler] = clazz()

        # Initialize modules
        for module, clazz  in PluginRegistry.modules.items():
            if module in PluginRegistry.handlers:
                PluginRegistry.modules[module] = PluginRegistry.handlers[module]
            else:
                PluginRegistry.modules[module] = clazz()

        # Let handlers serve
        for handler, clazz in sorted(PluginRegistry.handlers.items(),
                key=lambda k: k[1]._priority_):

            if hasattr(clazz, 'serve'):
                clazz.serve()

        #NOTE: For component handler: list implemented interfaces
        #print(list(zope.interface.implementedBy(module)))

    @staticmethod
    def shutdown():
        """
        Call handlers stop() methods in order to grant a clean shutdown.
        """
        for clazz  in PluginRegistry.handlers.values():
            if hasattr(clazz, 'stop'):
                clazz.stop()
                del clazz

    @staticmethod
    def getInstance(name):
        """
        Return an instance of a registered class.

        =============== ============
        Parameter       Description
        =============== ============
        name            name of the class to get instance of
        =============== ============

        >>> from gosa.common.components import PluginRegistry
        >>> cr = PluginRegistry.getInstance("CommandRegistry")

        """
        if not name in PluginRegistry.modules:
            raise ValueError("no module '%s' available" % name)

        if isclass(PluginRegistry.modules[name]):
            return None

        return PluginRegistry.modules[name]
