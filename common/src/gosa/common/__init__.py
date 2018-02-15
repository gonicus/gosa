# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from zope.interface import Interface, implementer

__import__('pkg_resources').declare_namespace(__name__)
__version__ = __import__('pkg_resources').get_distribution('gosa.common').version
from gosa.common.env import Environment


class IBusClientAvailability(Interface):  # pragma: nocover

    def __init__(self, obj):
        pass


@implementer(IBusClientAvailability)
class BusClientAvailability(object):

    def __init__(self, client_id, state, type, hostname=None):
        self.client_id = client_id
        self.state = state
        self.type = type
        self.hostname = hostname
