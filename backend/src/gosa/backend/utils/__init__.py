# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import enum

from gosa.common.components.jsonrpc_utils import JSONDataHandler

__import__('pkg_resources').declare_namespace(__name__)


class BackendTypes(enum.Enum):
    unknown = 0
    active_master = 1
    standby_master = 2
    proxy = 3


class BackendTypesEncoder(JSONDataHandler):
    @staticmethod
    def encode(data):
        return {"__enum__": str(data), '__jsonclass__': 'gosa.backend.utils.BackendTypes'}

    @staticmethod
    def decode(data):
        name, member = data["__enum__"].split(".")
        return getattr(BackendTypes, member)

    @staticmethod
    def isinstance(data):
        return isinstance(data, BackendTypes)

    @staticmethod
    def canhandle():
        return "gosa.backend.utils.BackendTypes"
