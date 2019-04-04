# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import pkg_resources

from gosa.common.components import PluginRegistry
from gosa.common.utils import N_
from gosa.common.error import GosaErrorHandler as C


# Register the errors handled  by us
C.register_codes(dict(
    BACKEND_NOT_FOUND=N_("Backend '%(topic)s' not found"),
    ))


class ObjectBackendRegistry(object):
    instance = None
    backends = {}
    uuidAttr = "entryUUID"
    __index = None

    def __init__(self):
        # Load available backends
        for entry in pkg_resources.iter_entry_points("gosa.object.backend"):
            clazz = entry.load()
            ObjectBackendRegistry.backends[clazz.__name__] = clazz()

    def dn2uuid(self, backend, dn, from_db_only=False):
        uuid = ObjectBackendRegistry.backends[backend].dn2uuid(dn)
        if uuid is None and from_db_only is True:
            # fallback to db
            if self.__index is None:
                self.__index = PluginRegistry.getInstance("ObjectIndex")
            res = self.__index.search({'dn': dn}, {'uuid': 1})
            if len(res) == 1:
                uuid = res[0]['_uuid']
        return uuid

    def uuid2dn(self, backend, uuid, from_db_only=False):
        dn = ObjectBackendRegistry.backends[backend].uuid2dn(uuid)
        if dn is None and from_db_only is True:
            # fallback to db
            if self.__index is None:
                self.__index = PluginRegistry.getInstance("ObjectIndex")
            res = self.__index.search({'uuid': uuid}, {'dn': 1})
            if len(res) == 1:
                dn = res[0]['dn']
        return dn

    def get_timestamps(self, backend, dn):
        return ObjectBackendRegistry.backends[backend].get_timestamps(dn)

    @staticmethod
    def getInstance():
        if not ObjectBackendRegistry.instance:
            ObjectBackendRegistry.instance = ObjectBackendRegistry()

        return ObjectBackendRegistry.instance

    @staticmethod
    def getBackend(name):
        if not name in ObjectBackendRegistry.backends:
            raise ValueError(C.make_error("BACKEND_NOT_FOUND", name))

        return ObjectBackendRegistry.backends[name]
