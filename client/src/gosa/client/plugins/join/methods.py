# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

import re
import os
import gettext
import netifaces #@UnresolvedImport
import ConfigParser
import socket
import logging
from urlparse import urlparse
from pkg_resources import resource_filename #@UnresolvedImport
from urllib import quote_plus as quote
from clacks.common.components.zeroconf_client import ZeroconfClient
from clacks.common.components import AMQPServiceProxy
from clacks.common.components.jsonrpc_proxy import JSONRPCException
from clacks.common import Environment
from clacks.common.utils import dmi_system
from qpid.messaging.exceptions import ConnectionError
from Crypto.Cipher import AES
from base64 import b64decode


# Include locales
t = gettext.translation('messages', resource_filename("clacks.client", "locale"), fallback=True)
_ = t.ugettext


class join_method(object):
    """
    There are several ways to present the join process, that are

     * CLI
     * Curses
     * QT

    in the moment. By implementing the :class:`clacks.client.plugins.join.methods.join_method` interface,
    new ones (i.e. graphical) can simply be added. The resulting modules have to be
    registerd in the setuptools ``[gosa.client.join.module]`` section.

    The **priority** class member is used to order the join methods.
    """
    _url = None
    _need_config_refresh = False
    priority = None

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.uuid = dmi_system("uuid")
        self.mac = self.get_mac_address()
        self.domain = socket.getfqdn().split('.', 1)[1]
        self.get_service()

    def url_builder(self, username, password):
        username = quote(username)
        password = quote(password)
        u = urlparse(self.url)
        #pylint: disable=E1101
        return "%s://%s:%s@%s%s" % (u.scheme, username, password, u.netloc, u.path)

    def test_login(self):
        # No key set? Go away...
        if not self.key:
            self.log.warning("no machine key available - join required")
            return False

        # Prepare URL for login
        url = self.url_builder(self.svc_id, self.key)

        # Try to log in with provided credentials
        try:
            AMQPServiceProxy(url)
            self.log.debug("machine key is valid")
            return True
        except ConnectionError:
            self.log.warning("machine key is invalid - join required")
            return False

    def join(self, username, password, data=None):

        # Prepare URL for login
        url = self.url_builder(username, password)

        # Try to log in with provided credentials
        try:
            proxy = AMQPServiceProxy(url)
        except ConnectionError as e:
            self.log.error("connection to AMQP failed: %s" % str(e))
            self.show_error(_("Cannot join client: check user name or password!"))
            return None

        # Try to join client
        try:
            key, uuid = proxy.joinClient(u"" + self.uuid, self.mac, data)
        except JSONRPCException as e:
            self.show_error(e.error.capitalize())
            self.log.error(e.error)
            return None

        # If key is present, write info back to file
        if key:
            self.log.debug("client '%s' joined with key '%s'" % (self.uuid, key))
            config = os.path.join(self.env.config.get("core.config"), "config")
            parser = ConfigParser.RawConfigParser()
            parser.read(config)

            # Section present?
            try:
                url = parser.get("amqp", "url")
            except ConfigParser.NoSectionError:
                parser.add_section("amqp")
            except ConfigParser.NoOptionError:
                pass

            # Set url and key
            parser.set("amqp", "url", self.url)
            parser.set("core", "id", uuid)
            parser.set("amqp", "key", key)

            # Write back to file
            with open(config, "wb") as f:
                parser.write(f)

        return key

    def decrypt(self, key, data):
        key_pad = AES.block_size - len(key) % AES.block_size
        if key_pad != AES.block_size:
            key += chr(key_pad) * key_pad
        data = AES.new(key, AES.MODE_ECB).decrypt(data)
        return data[:-ord(data[-1])]

    def get_service_from_config(self):
        url = self.env.config.get("amqp.url", default=None)
        sys_id = self.env.config.get("client.id", default=None)
        key = self.env.config.get("amqp.key", default=None)
        return (url, sys_id, key)

    def discover(self):
        print _("Searching for service provider...")
        return ZeroconfClient.discover(['_amqps._tcp', '_amqp._tcp'], domain=self.domain)[0]

    def get_service(self):

        # Try to load url/key from configuration
        (svc_url, svc_id, svc_key) = self.get_service_from_config()
        if svc_url and svc_key:
            self.svc_id = svc_id if svc_id else self.uuid
            self.url = svc_url
            self.key = svc_key
            return

        # Check for svc information
        with open("/proc/cmdline", "r") as f:
            line = f.readlines()[0]

        # Scan command line for svc_ entries
        for dummy, var, data in re.findall(r"(([a-z0-9_]+)=([^\s]+))",
            line, flags=re.IGNORECASE):

            # Save relevant values
            if var == "svc_url":
                svc_url = data
            if var == "svc_key":
                tmp = self.decrypt(self.uuid.replace("-", ""), b64decode(data))
                svc_id = tmp[0:36]
                svc_key = tmp[36:]
                self._need_config_refresh = True

        # If there's no url, try to find it using zeroconf
        if not svc_url:
            svc_url = self.discover()

        self.svc_id = svc_id
        self.url = svc_url
        self.key = svc_key

        if self._need_config_refresh:
            config = self.env.config.get("core.config")
            parser = ConfigParser.RawConfigParser()
            parser.read(config)

            # Section present?
            try:
                parser.get("amqp", "url")
            except ConfigParser.NoSectionError:
                parser.add_section("amqp")

            # Set url and key
            parser.set("amqp", "url", self.url)
            parser.set("core", "id", self.svc_id)
            parser.set("amqp", "key", self.key)

            # Write back to file
            with open(config, "wb") as f:
                parser.write(f)

    def get_mac_address(self):
        for interface in netifaces.interfaces():
            i_info = netifaces.ifaddresses(interface)

            # Skip lo interfaces
            if i_info[netifaces.AF_LINK][0]['addr'] == '00:00:00:00:00:00':
                continue

            # Skip lo interfaces
            if not netifaces.AF_INET in i_info:
                continue

            return i_info[netifaces.AF_LINK][0]['addr']

        return None

    def show_error(self, error):
        """
        *show_error* is the function used to show messages to the user. It
        needs to be implemented.

        ========== ============
        Parameter  Description
        ========== ============
        error      The error string
        ========== ============
        """
        raise NotImplemented("show_error not implemented")

    def join_dialog(self):
        """
        This dialog presents the join dialog aquiring the username
        and the password of a person capable to join the client. It
        must call the :meth:`clacks.client.plugins.join.methods.join_method.join`
        method and loop until success or abort itself.
        """
        raise NotImplemented("join_dialog not implemented")

    @staticmethod
    def available():
        """
        This method can check if the current method is available
        on the system. It is used to avoid that i.e. a framebuffer
        dialog will show up when there's no framebuffer.

        ``Returns``: True if available
        """
        return False
