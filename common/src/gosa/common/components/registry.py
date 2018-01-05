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

import itertools
from lxml import objectify

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
    _event_parser = None

    def __init__(self, component=None):
        env = Environment.getInstance()
        self.env = env
        self.log = logging.getLogger(__name__)
        self.log.debug("initializing plugin registry")

        # Load common event resources
        base_dir = resource_filename('gosa.common', 'data/events') + os.sep

        files = [ev for ev in resource_listdir('gosa.common', 'data/events')
                if ev[-4:] == '.xsd']
        for f in files:
            event = os.path.splitext(f)[0]
            self.log.debug("adding common event '%s'" % event)
            PluginRegistry.evreg[event] = os.path.join(base_dir, f)

        # Get module from setuptools
        if component is None:
            components = ["gosa.plugin", "gosa.%s.plugin" %
                          self.env.config.get("core.mode", default="backend")]
        else:
            components = [component]
        print(components)
        for comp in components:
            for entry in iter_entry_points(comp):
                module = entry.load()
                self.log.info("module %s included" % module.__name__)
                PluginRegistry.modules[module.__name__] = module

                # Save interface handlers
                # pylint: disable=E1101
                if IInterfaceHandler.implementedBy(module):
                    self.log.debug("registering handler module %s" % module.__name__)
                    PluginRegistry.handlers[module.__name__] = module

        # Register module events
        for module, clazz  in PluginRegistry.modules.items():

            # Check for event resources
            if resource_isdir(clazz.__module__, 'data/events'):
                base_dir = resource_filename(clazz.__module__, 'data/events')

                for filename in resource_listdir(clazz.__module__, 'data/events'):
                    if filename[-4:] != '.xsd':
                        continue
                    event = os.path.splitext(filename)[0]
                    if not event in PluginRegistry.evreg:
                        PluginRegistry.evreg[event] = os.path.join(base_dir, filename)
                        self.log.debug("adding module event '%s'" % event)

        # Initialize component handlers
        for handler, clazz in PluginRegistry.handlers.items():
             PluginRegistry.handlers[handler] = clazz()

        # Initialize modules
        for module, clazz  in PluginRegistry.modules.items():
            if module in PluginRegistry.handlers:
                PluginRegistry.modules[module] = PluginRegistry.handlers[module]
            else:
                if hasattr(clazz, 'get_instance'):
                    PluginRegistry.modules[module] = clazz.get_instance()
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
        for clazz in PluginRegistry.handlers.values():
            if hasattr(clazz, 'stop'):
                clazz.stop()
            del clazz

        PluginRegistry.handlers = {}

        for clazz in PluginRegistry.modules.values():
            del clazz

        PluginRegistry.modules = {}

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

    @staticmethod
    def getEventSchema():
        stylesheet = resource_filename('gosa.common', 'data/events/events.xsl')
        eventsxml = "<events>"

        for file_path in PluginRegistry.evreg.values():

            # Build a tree of all event paths
            eventsxml += '<path name="%s">%s</path>' % (os.path.splitext(os.path.basename(file_path))[0], file_path)

        eventsxml += '</events>'

        # Parse the string with all event paths
        eventsxml = StringIO(eventsxml)
        xml_doc = etree.parse(eventsxml)

        # Parse XSLT stylesheet and create a transform object
        xslt_doc = etree.parse(stylesheet)
        transform = etree.XSLT(xslt_doc)

        # Transform the tree of all event paths into the final XSD
        res = transform(xml_doc)
        return str(res)

    @staticmethod
    def getEventParser():
        if PluginRegistry._event_parser is None:
            # Initialize parser
            schema_root = etree.XML(PluginRegistry.getEventSchema())
            schema = etree.XMLSchema(schema_root)
            PluginRegistry._event_parser = objectify.makeparser(schema=schema)

        return PluginRegistry._event_parser

