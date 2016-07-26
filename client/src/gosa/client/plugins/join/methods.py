# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import re
import os
import sys
import gettext
import netifaces #@UnresolvedImport
import configparser as ConfigParser
import socket
import logging
from urllib.parse import urlparse
from pkg_resources import resource_filename #@UnresolvedImport
from urllib.parse import quote_plus as quote
from urllib.request import HTTPError
from gosa.common.components import JSONServiceProxy, JSONRPCException
from gosa.common import Environment
from gosa.common.utils import dmi_system
from gosa.common.utils import N_
from Crypto.Cipher import AES
from base64 import b64decode


# Include locales
t = gettext.translation('messages', resource_filename("gosa.client", "locale"), fallback=True)
_ = t.gettext


class join_method(object):
    """
    There are several ways to present the join process, that are

     * CLI
     * Curses
     * QT

    in the moment. By implementing the :class:`gosa.client.plugins.join.methods.join_method` interface,
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
        try:
            self.domain = socket.getfqdn().split('.', 1)[1]
        except IndexError:
            self.log.warning("system has no proper DNS domain")
            self.domain = socket.getfqdn().split('.', 1)[0] + ".local"

        self.get_service()

    def test_login(self):
        # No key set? Go away...
        if not self.key:
            self.log.warning("no machine key available - join required")
            return False

        # Prepare URL for login
        url = urlparse(self.url)

        # Try to log in with provided credentials
        connection = '%s://%s%s' % (url.scheme, url.netloc, url.path)
        proxy = JSONServiceProxy(connection)

        # Try to log in
        try:
            if not proxy.login(self.svc_id, self.key):
                self.log.warning("machine key is invalid - join required")
                return False
        except HTTPError as e:
            if e.code == 401:
                self.log.error("connection to GOsa backend failed")
                self.show_error(_("Cannot join client: check user name or password!"))
                return False
            else:
                print(e)
                sys.exit(1)
        except Exception as e:
            print(e)
            sys.exit(1)

        self.log.debug("machine key is valid")
        return True

    def join(self, username, password, data=None):

        # Prepare URL for login
        url = urlparse(self.url)

        # Try to log in with provided credentials
        connection = '%s://%s%s' % (url.scheme, url.netloc, url.path)
        proxy = JSONServiceProxy(connection)

        # Try to log in
        try:
            if not proxy.login(username, password):
                self.log.error("connection to GOsa backend failed")
                self.show_error(_("Cannot join client: check user name or password!"))
                return False
        except HTTPError as e:
            if e.code == 401:
                self.log.error("connection to GOsa backend failed")
                self.show_error(_("Cannot join client: check user name or password!"))
                return False
            else:
                print(e)
                sys.exit(1)

        except Exception as e:
            print(e)
            sys.exit(1)

        # Try to join client
        try:
            key, uuid = proxy.joinClient("" + self.uuid, self.mac, data)
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
                url = parser.get("jsonrpc", "url")
            except ConfigParser.NoSectionError:
                parser.add_section("jsonrpc")
            except ConfigParser.NoOptionError:
                pass

            # Set url and key
            parser.set("jsonrpc", "url", self.url)
            parser.set("core", "id", uuid)
            parser.set("jsonrpc", "key", key)

            # Write back to file
            with open(config, "w") as f:
                parser.write(f)

        return key

    def decrypt(self, key, data):
        key_pad = AES.block_size - len(key) % AES.block_size
        if key_pad != AES.block_size:
            key += chr(key_pad) * key_pad
        data = AES.new(key, AES.MODE_ECB).decrypt(data)
        return data[:-ord(data[-1])]

    def get_service_from_config(self):
        url = self.env.config.get("mqtt.url", default=None)
        sys_id = self.env.config.get("client.id", default=None)
        key = self.env.config.get("mqtt.key", default=None)
        return (url, sys_id, key)

    def discover(self):
        #TODO
        print(N_("Searching for service provider..."))
        return None

    def get_service(self):

        # Try to load url/key from configuration
        (svc_url, svc_id, svc_key) = self.get_service_from_config()
        if svc_url and svc_key:
            self.svc_id = svc_id if svc_id else self.uuid
            self.url = svc_url
            self.key = svc_key
            return

        # Check for svc in CLI command line
        if len(sys.argv) == 2:
            svc_url = sys.argv[1]

        # Check for svc in kernel command line
        if not svc_url:
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

        # If there's no url, try to find it using DNS
        if not svc_url:
            svc_url = self.discover()

        if not svc_url:
            self.log.error("no service URL specified")
            self.show_error(_("Cannot join client: please provide a service URL!"))
            sys.exit(1)

        self.svc_id = svc_id
        self.url = svc_url
        self.key = svc_key

        if self._need_config_refresh:
            config = self.env.config.get("core.config")
            parser = ConfigParser.RawConfigParser()
            parser.read(config)

            # Section present?
            try:
                parser.get("jsonrpc", "url")
            except ConfigParser.NoSectionError:
                parser.add_section("jsonrpc")

            # Set url and key
            parser.set("jsonrpc", "url", self.url)
            parser.set("core", "id", self.svc_id)
            parser.set("jsonrpc", "key", self.key)

            # Write back to file
            with open(config, "w") as f:
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
        must call the :meth:`gosa.client.plugins.join.methods.join_method.join`
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
