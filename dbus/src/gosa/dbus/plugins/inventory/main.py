# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
.. _dbus-fusion:

Fusioninventory module
~~~~~~~~~~~~~~~~~~~~~~

To. Do.
"""

import os
import re
import shutil
import subprocess
import dbus.service
import hashlib
import logging
from pkg_resources import resource_filename #@UnresolvedImport
from lxml import etree, objectify
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.dbus import get_system_bus
from base64 import b64encode


class InventoryException(Exception):
    pass


class DBusInventoryHandler(dbus.service.Object, Plugin):
    """ This handler collect client inventory data """

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/org/gosa/inventory')
        self.env = Environment.getInstance()

    @dbus.service.method('org.gosa', in_signature='', out_signature='s')
    def inventory(self):
        """
        Start inventory client and transform the results into a gosa usable way.

        We should support other invetory clients, later.
        """

        # Added other report types here
        result = self.load_from_fusion_agent()
        return result

    def load_from_fusion_agent(self):
        # Execute the inventory agent.
        try:
            content = subprocess.check_output(["fusioninventory-agent", "--local", "-"], stderr=subprocess.DEVNULL)

        except OSError as e:
            log = logging.getLogger(__name__)
            log.error("failed to invoke fusion-inventory agent: %s" % str(e))
            return None

        # Try to extract HardwareUUID
        tmp = objectify.fromstring(content)
        huuid = tmp.xpath('/REQUEST/CONTENT/HARDWARE/UUID/text()')[0]

        # Open the first found result file and transform it into a gosa usable
        # event-style xml.
        try:
            xml_doc = etree.fromstring(content)
            xslt_doc = etree.parse(resource_filename("gosa.dbus.plugins.inventory", "data/fusionToGosa.xsl"))
            transform = etree.XSLT(xslt_doc)
            result = etree.tostring(transform(xml_doc)).decode()
        except Exception as e:
            raise InventoryException("Failed to read and transform fusion-inventory-agent results (%s)!")

        # Add the ClientUUID and the encoded HardwareUUID to the result
        #result = re.sub("%%CUUID%%", self.env.uuid, result)
        result = re.sub("%%HWUUID%%", self.hash_hardware_uuid(huuid).decode(), result)
        #result = re.sub("%%SCHEMALOC%%", resource_filename("gosa.plugins.goto", "data/events/Inventory.xsd"), result)

        return result

    def hash_hardware_uuid(self, huuid):
        """
        Hash the hardware uuid,  it is not secure to send the it as clear text.
        """
        sha = hashlib.sha256()
        sha.update(huuid.encode())
        return(b64encode(sha.digest()))
