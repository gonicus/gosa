# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
.. _client-dbus:

D-Bus Command Proxy
^^^^^^^^^^^^^^^^^^^

The D-Bus Command proxy automatically exports all registered D-Bus methods to the
GOsa command-registry and thus allows calling them directly without having a
client plugin created for them.


The gosa-client receives its commands form the GOsa backend, but it cannot
execute commands that require root privileges, so it communicates with the
gosa-dbus module which runs as root on the same machine.

>>> Server             Client
>>> -----------------------------------
>>> Agent --> Mqtt --> Client
>>>                    Client --> DBus --> GOsa-DBus

Normally you would write a client-plugin for each command that has to be forwarded to
the gosa-dbus. With the D-Bus Command Proxy you don't have to do this anymore,
because all methods that match a given naming syntax will be exported automatically.

For example the "GOsa D-Bus System Service Plugin" methods are exported without a
client plugin.


Which methods are exported?
^^^^^^^^^^^^^^^^^^^^^^^^^^^

All methods of the service 'org.gosa' with any path are exported, if they do not start
with ``_`` or ``:``.

Exported methods are prefixed with ``dbus_`` e.g. the ``wake_on_lan`` method is then
accessible by calling ``dbus_wake_on_lan``. (:class:`gosa.dbus.plugins.wakeonlan.main.DBusWakeOnLanHandler`.)


>>> proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "dbus_wake_on_lan", "<mac>")



"""


# -*- coding: utf-8 -*-
from _dbus_bindings import INTROSPECTABLE_IFACE
from dbus.exceptions import DBusException

import os
import logging
from lxml import etree
from zope.interface import implementer
from gosa.common.handler import IInterfaceHandler
from gosa.common.components import Plugin, PluginRegistry
from gosa.common.components.dbus_runner import DBusRunner


class DBusProxyException(Exception):
    pass


@implementer(IInterfaceHandler)
class DBUSProxy(Plugin):
    """
    DBus service plugin.

    This plugin is a proxy for dbus-methods registered by the
    gosa-dbus.

    Each method that is registered for service 'org.gosa'
    can be accessed by calling callDBusMethod, except for
    anonymous methods (those starting with _ or :)
    """
    _target_ = 'service'
    _priority_ = 5

    log = None
    bus = None
    methods = None

    # DBus proxy object
    gosa_dbus = None

    # Type map for signature checking
    _type_map = {
                 'as': [list],
                 'a{ss}': [dict],
                 'i': [int],
                 'n': [int],
                 'x': [int],
                 'q': [int],
                 'y': [chr],
                 'u': [int],
                 't': [int],
                 'b': [bool],
                 's': [str],
                 'o': [object],
                 'd': [float]}

    def __init__(self):
        self.log = logging.getLogger(__name__)

        # Get a dbus proxy and check if theres a service registered called 'org.gosa'
        # if not, then we can skip all further processing. (The gosa-dbus seems not to be running)
        self.__dr = DBusRunner.get_instance()
        self.bus = self.__dr.get_system_bus()
        self.methods = {}

    def __dbus_proxy_monitor(self, bus_name):
        """
        This method monitors the DBus service 'org.gosa' and whenever there is a
        change in the status (dbus closed/startet) we will take notice.
        And can stop or restart singature checking.
        """
        if "org.gosa" in self.bus.list_names():
            if self.gosa_dbus:
                del(self.gosa_dbus)
            self.gosa_dbus = self.bus.get_object('org.gosa', '/org/gosa/shell')
            self.gosa_dbus.connect_to_signal("_signatureChanged", self.__signatureChanged_received, dbus_interface="org.gosa")
            self.log.info("established dbus connection")
            self.__signatureChanged_received(None)

            # Trigger resend of capapability event
            ccr = PluginRegistry.getInstance('ClientCommandRegistry')
            ccr.register("listDBusMethods", 'DBUSProxy.listDBusMethods', [], [], 'This method lists all callable dbus methods')
            ccr.register("callDBusMethod", 'DBUSProxy.callDBusMethod', [], ['method', '*args'],
                         'This method allows to access registered dbus methods by forwarding methods calls')
            mqtt = PluginRegistry.getInstance('MQTTClientService')
            mqtt.reAnnounce()
        else:
            if self.gosa_dbus:
                del(self.gosa_dbus)
                self.__signatureChanged_received(None)
                self.log.info("lost dbus connection")

                # Trigger resend of capapability event
                ccr = PluginRegistry.getInstance('ClientCommandRegistry')
                ccr.unregister("listDBusMethods")
                ccr.unregister("callDBusMethod")
                mqtt = PluginRegistry.getInstance('MQTTClientService')
                mqtt.reAnnounce()
            else:
                self.log.info("no dbus connection")

    def __signatureChanged_received(self, filename):
        """
        This is the callback method for our DBus-Event registration for '_signatureChanged'
        """
        self.reload_signatures()

    def reload_signatures(self):
        """
        Reloads the dbus signatures.
        """

        to_register = {}
        to_unregister = {}

        if not self.gosa_dbus:
            self.log.debug("no dbus service registered for '%s' - is gosa-dbus running?" % ("org.gosa"))
            to_unregister = self.methods
            self.methods = {}
        else:
            try:
                self.log.debug('loading dbus-methods registered by GOsa (introspection)')
                new_methods = self._call_introspection("org.gosa", "/")

                # Detect new methods
                for meth in new_methods:
                    if meth not in self.methods or self.methods[meth]['args'] != new_methods[meth]['args']:
                        to_register[meth] = new_methods[meth]

                # Find removed methods
                for meth in self.methods:
                    if not meth in new_methods:
                        to_unregister[meth] = self.methods[meth]

                self.methods = new_methods
                self.log.debug("found %s registered dbus methods" % (str(len(self.methods))))

            except DBusException as exception:
                self.log.debug("failed to load dbus methods: %s" % (str(exception)))

        # (Re-)register the methods we've found
        ccr = PluginRegistry.getInstance('ClientCommandRegistry')
        for name in to_register:
            ccr.register(name, 'DBUSProxy.callDBusMethod', [name], ['(signatur)'], 'docstring')
        for name in to_unregister:
            ccr.unregister(name)

        # Trigger resend of capapability event
        mqtt = PluginRegistry.getInstance('MQTTClientService')
        mqtt.reAnnounce()

    def _call_introspection(self, service, path, methods=None):
        """
        Introspects the dbus service with the given service and path.

        =============== ================
        key             description
        =============== ================
        service         The dbus service we want to introspect. (e.g. org.gosa)
        path            The path we want to start introspection from. (e.g. '/' or '/org/gosa')
        methods         A dictionary used internaly to build up a result.
        =============== ================

        This method returns a dictionary containing all found methods
        with their path, service and parameters.
        """

        # Start the 'Introspection' method on the dbus.
        data = self.bus.call_blocking(service, path, INTROSPECTABLE_IFACE,
                'Introspect', '', ())

        # Return parsed results.
        if methods == None:
            methods = {}
        return self._introspection_handler(data, service, path, methods)

    def _introspection_handler(self, data, service, path, methods):
        """
        Parses the result of the dbus method 'Introspect'.

        It will recursivly load information for newly received paths and methods,
        by calling '_call_introspection'.

        =============== ================
        key             description
        =============== ================
        data            The result of the dbus method call 'Introspect'
        service         The dbus service that was introspected
        path            The path we introspected
        methods         A dictionary used internaly to build up a result.
        =============== ================
        """

        # Transform received XML data into a python object.
        res = etree.fromstring(data)

        # Check for a xml-node containing dbus-method information.
        #
        # It looks like this:
        #       <node name="/org/gosa/notify">
        #         <interface name="org.gosa">
        #           <method name="notify_all">
        #             <arg direction="in"  type="s" name="title" />
        #             ...
        #           </method>
        #         </interface>
        #       ...
        #       </node>
        if res.tag == "node" and res.get('name'):

            # Get the path name this method is registered to (e.g. /org/gosa/notify)
            path = res.get('name')

            # add all found methods to the list of known ones
            for entry in res:
                if entry.tag == "interface" and entry.get("name") == service:
                    for method in entry.iterchildren():

                        # Skip method names that start with _ or : (anonymous methods)
                        m_name = method.get('name')
                        if m_name.startswith('_') or m_name.startswith(':'):
                            continue

                        # Mark dbus method with a 'dbus' prefix to be able to distinguish between
                        # client methods and proxied dbus methods
                        m_name = "dbus_" + m_name

                        # Check if this method name is already registered.
                        if m_name in methods:
                            raise DBusProxyException("Duplicate dbus method found '%s'! See (%s, %s)" % (
                                m_name, path, methods[m_name]['path']))

                        # Append the new method to the list og known once.
                        methods[m_name] = {}
                        methods[m_name]['path'] = path
                        methods[m_name]['service'] = service
                        methods[m_name]['args'] = ()

                        # Extract method parameters
                        for arg in method.iterchildren():
                            if arg.tag == "arg" and arg.get("direction") == "in":
                                argument = (arg.get('name'), arg.get('type'))
                                methods[m_name]['args'] += (argument,)

        # Check for a xml-node which introduces new paths
        #
        # It will look like this:
        #       <node>
        #         <node name="inventory"/>
        #         <node name="notify"/>
        #         <node name="service"/>
        #         <node name="wol"/>
        #       </node>
        #
        # Request information about registered services by calling 'Introspect' for each path again
        else:
            for entry in res:
                if entry.tag == "node":
                    sname = entry.get('name')
                    self._call_introspection(service, os.path.join(path, sname), methods)

        return methods

    def serve(self):
        """
        This method registeres all known methods to the command registry.
        """
        # Register ourselfs for bus changes on org.gosa
        self.bus.watch_name_owner("org.gosa", self.__dbus_proxy_monitor)

        ccr = PluginRegistry.getInstance('ClientCommandRegistry')
        for name in self.methods.keys():
            ccr.register(name, 'DBUSProxy.callDBusMethod', [name], ['(signatur)'], 'docstring')

    def listDBusMethods(self):
        """ This method lists all callable dbus methods """
        return self.methods

    def callDBusMethod(self, method, *args):
        """ This method allows to access registered dbus methods by forwarding methods calls """

        """
        ======= ==============
        Key     Description
        ======= ==============
        method  The name of the method to call on dbus side.
        ...     A list of parameters for the method call.
        ======= ==============
        """

        # Check if we've got a dbus proxy object right now.
        if not self.gosa_dbus:
            raise DBusProxyException("the gosa-dbus seems not to be running, skipped execution")

        # Check given method and parameters
        self._check_parameters(method, args)

        # Now call the dbus method with the given list of paramters
        mdata = self.methods[method]
        cdbus = self.bus.get_object(mdata['service'], mdata['path'])

        # Remove the method prefix again 'dbus_'
        method = method[5::]
        method = cdbus.get_dbus_method(method, dbus_interface=mdata['service'])
        returnval = method(*args)
        return returnval

    def _check_parameters(self, method, args):
        """
        Checks if the given list of arguments (args) are compatible with the
        given dbus-method (method)

        ======= ==============
        Key     Description
        ======= ==============
        method  The name of the method.
        args    The list of arguments to check for.
        ======= ==============
        """

        # Check if the requested dbus method is registered.
        if method not in self.methods:
            raise NotImplementedError(method)

        # Get list of required argument
        m_args = self.methods[method]['args']
        given = ""
        args = list(args)

        # Check each argument
        cnt = 0

        for argument, arg_type in m_args:
            cnt += 1

            # Does the argument exists
            try:
                given = args.pop(0)
            except IndexError:
                raise TypeError("the parameter '%s' is missing" % argument)

            # Check if the given argument matches the required signature type
            found = True
            if arg_type in self._type_map:
                found = False
                for p_type in self._type_map[arg_type]:
                    if isinstance(given, p_type):
                        found = True
            else:
                raise TypeError("the parameter %s (%s) is of unknown type. Type is: %s" % (argument, str(cnt), arg_type))

            if not found:
                types = ", ".join(map(lambda x: x.__name__, self._type_map[arg_type]))
                raise TypeError("the parameter %s (%s) is of invalid type. Expected: %s" % (argument, str(cnt), types))

        # We received more arguments than required by the dbus method...
        if len(args):
            raise TypeError("%s() takes exactly %s arguments (%s given)" % (method, len(m_args), cnt + len(args)))
