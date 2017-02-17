# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from zope.interface import implementer
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.components import PluginRegistry
from gosa.common.handler import IInterfaceHandler
from gosa.common.utils import N_


@implementer(IInterfaceHandler)
class ZarafaRPCMethods(Plugin):

    _target_ = 'gui'
    _priority_ = 80

    @Command(__help__=N_("Returns a list with all selectable zarafa mail servers"))
    def getZarafaMailServers(self):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'extension': 'ZarafaServer', 'zarafaAccount': 'True'},
            {'cn': 1, 'zarafaAccount': 1})

        res = list(set([x['cn'][0] for x in res]))
        res.sort()

        return res
