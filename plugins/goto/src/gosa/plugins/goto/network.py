# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import re
import socket
import ipaddress
import subprocess
from netaddr import EUI, NotRegisteredError
from gosa.common.components import Plugin
from gosa.common.utils import N_
from gosa.common.components.command import Command


class NetworkUtils(Plugin):
    """
    Module containing network utilities like DNS/MAC resolving and
    manufacturer resolving.
    """
    _target_ = 'goto'
    oui = None

    @Command(__help__=N_("Resolve network address to a mac / dns name tupel."))
    def networkCompletion(self, name):
        protocolAddress = socket.gethostbyname(name)
        networkAddress = self.getMacFromIP(protocolAddress)
        return {'ip': protocolAddress, 'mac': networkAddress}

    def __sendPacket(self, protocolAddress):
        ip = str(ipaddress.ip_address(protocolAddress))
        p = subprocess.Popen(['ping', ip, '-c1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

    def getMacFromARP(self, protocolAddress):
        ip = str(ipaddress.ip_address(protocolAddress))

        # Call arp command and try to find a suitable entry
        p = subprocess.Popen(['arp', '-n'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

        for line in out.decode('utf-8').split('\n'):
            match = line.split()
            if len(match):
                try:
                    _ip = ipaddress.ip_address(match[0])
                    if str(_ip) == str(ip):
                        return match[2]
                except ValueError:
                    pass

        return None

    def getMacFromIP(self, protocolAddress):
        result = self.getMacFromARP(protocolAddress)
        if not result:
            self.__sendPacket(protocolAddress)
            result = self.getMacFromARP(protocolAddress)
        return str(result)

    @Command(__help__=N_("Resolve MAC address to the producer of the network card if possible."))
    def getMacManufacturer(self, mac):
        """
        This function uses the ieee file provided at
        http://standards.ieee.org/regauth/oui/oui.txt
        """
        try:
            mac = EUI(mac)
            oui = mac.oui.registration()
        except NotRegisteredError:
            return None

        # pylint: disable=E1101
        return oui.org
