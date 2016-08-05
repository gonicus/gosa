# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""

.. _client-fusion:

Description
^^^^^^^^^^^

This plugin is used to create inventory information for the client.

It uses the dbus method ``inventory`` which is exported by the
gosa-dbus-plugin :class:`gosa.dbus.plugins.inventory.main.DBusInventoryHandler` to receive client inventory
information for the client.

With the method ``request_inventory`` you can trigger an update of the client inventory
dataset on the server. The client will then collect all information and then send them
to the gosa-backend.

>>> proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "request_inventory")

If you just want to see the inventory result without sending the result to the server, you
can call the dbus method directly:

>>> proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "dbus_inventory")

"""

# -*- coding: utf-8 -*-
import hashlib
import re
import logging
from threading import Thread
from lxml import etree
from dbus import DBusException
from io import StringIO
from gosa.common import Environment
from gosa.common.components import PluginRegistry, Plugin
from gosa.common.components.dbus_runner import DBusRunner
from pkg_resources import resource_filename #@UnresolvedImport


class Inventory(Plugin):
    """
    Utility class that contains methods needed to handle WakeOnLAN
    notification functionality.
    """
    _target_ = 'inventory'
    bus = None
    gosa_dbus = None

    def __init__(self):
        env = Environment.getInstance()
        self.env = env
        self.log = logging.getLogger(__name__)

        # Register ourselfs for bus changes on org.gosa
        dr = DBusRunner.get_instance()
        self.bus = dr.get_system_bus()
        self.bus.watch_name_owner("org.gosa", self.__dbus_proxy_monitor)

    def __dbus_proxy_monitor(self, bus_name):
        """
        This method monitors the DBus service 'org.gosa' and whenever there is a
        change in the status (dbus closed/startet) we will take notice.
        And can register or unregister methods to the dbus
        """
        if "org.gosa" in self.bus.list_names():
            if self.gosa_dbus:
                del self.gosa_dbus

            # Trigger resend of capapability event
            self.gosa_dbus = self.bus.get_object('org.gosa', '/org/gosa/inventory')
            ccr = PluginRegistry.getInstance('ClientCommandRegistry')
            ccr.register("request_inventory", 'Inventory.request_inventory', [], ['old_checksum=None'], 'Request client inventory information')
            mqtt = PluginRegistry.getInstance('MQTTClientService')
            mqtt.reAnnounce()
            self.log.info("established dbus connection")

        else:
            if self.gosa_dbus:
                del(self.gosa_dbus)

                # Trigger resend of capapability event
                ccr = PluginRegistry.getInstance('ClientCommandRegistry')
                ccr.unregister("request_inventory")
                mqtt = PluginRegistry.getInstance('MQTTClientService')
                mqtt.reAnnounce()
                self.log.info("lost dbus connection")
            else:
                self.log.info("no dbus connection")

    def request_inventory(self, old_checksum=None):
        """ Request client inventory information """

        # Get BUS connection
        try:
            # Request inventory result from dbus-client (He is running as root and can do much more than we can)
            self.log.info("retrieving inventory data from dbus...")
            result = self.gosa_dbus.inventory(dbus_interface="org.gosa")

        except DBusException as e:
            self.log.debug("failed to call dbus method 'inventory': %s" % (str(e)))
            return False

        # Remove time base or frequently changing values (like processes) from the
        # result to generate a useable checksum.
        # We use a XSL file which reads the result and skips some tags.
        xml_doc = etree.parse(StringIO(result))

        checksum_doc = etree.parse(resource_filename("gosa.client.plugins.inventory", "data/xmlToChecksumXml.xsl"))
        check_trans = etree.XSLT(checksum_doc)
        checksum_result = check_trans(xml_doc)

        # Once we've got a 'clean' result, create the checksum.
        m = hashlib.md5()
        m.update(etree.tostring(checksum_result))
        checksum = m.hexdigest()

        #TODO Debug - remove me later
        import datetime
        open("/tmp/inventory_%s" % (str(datetime.datetime.now()),), 'wb').write(etree.tostring(checksum_result, pretty_print=True))

        # Just don't do anything with the remote if the checksum did
        # not change
        if checksum == old_checksum:
            self.log.info("skipped sending inventory data, nothing changed!")
            return

        # Insert the checksum into the resulting event
        result = re.sub(r"%%CHECKSUM%%", checksum, result)

        def runner():
            # Establish mqtt connection
            self.log.info("sending inventory data!")
            mqtt = PluginRegistry.getInstance("MQTTClientHandler")
            mqtt.send_message(str(result))

        self.__thread = Thread(target=runner)
        self.__thread.start()
        return True
