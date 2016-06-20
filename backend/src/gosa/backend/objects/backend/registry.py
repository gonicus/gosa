# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import pkg_resources
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

    def __init__(self):
        # Load available backends
        for entry in pkg_resources.iter_entry_points("gosa.object.backend"):
            clazz = entry.load()
            ObjectBackendRegistry.backends[clazz.__name__] = clazz()

    def dn2uuid(self, backend, dn):
        return ObjectBackendRegistry.backends[backend].dn2uuid(dn)

    def uuid2dn(self, backend, uuid):
        return ObjectBackendRegistry.backends[backend].uuid2dn(uuid)

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
