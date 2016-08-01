# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import socket
import logging
import dns.resolver


def find_service():
    """
    Search for DNS SRV records like these:

    _gosa-api._tcp.example.com. 3600  IN  SRV  10  0  8000  gosa.intranet.gonicus.de.
    _gosa-ssl-api._tcp.example.com. 3600  IN  SRV  10  0  8000  gosa.intranet.gonicus.de.
    _gosa-bus._tcp.example.com. 3600  IN  SRV  10  50  1883  gosa-bus.intranet.gonicus.de.
                                      IN  SRV  10  60  1883  gosa-bus2.intranet.gonicus.de.
    _gosa-ssl-bus._tcp.example.com. 3600  IN  SRV  10  50  8883  gosa-bus.intranet.gonicus.de.
                                      IN  SRV  10  60  8883  gosa-bus2.intranet.gonicus.de.
    """
    log = logging.getLogger(__name__)

    fqdn = socket.getfqdn()
    if not "." in fqdn:
        log.error("invalid DNS configuration: there is no domain configured for this client")

    res = []
    for part in ["-ssl-api", "-ssl-bus", "-api", "-bus"]:
        try:
            log.debug("looking for DNS SRV records: _gosa%s._tcp" % part)
            for data in dns.resolver.query("_gosa%s._tcp" % part, "SRV"):
                res.append((data.priority, data.weight, str(data.target)[:-1]))

        except dns.resolver.NXDOMAIN:
            pass

    # Sort by priorty
    sorted(res, key=lambda entry: entry[1])
    return [entry[2] for entry in res]
