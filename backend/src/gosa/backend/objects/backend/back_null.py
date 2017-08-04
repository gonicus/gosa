# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from gosa.backend.objects.backend import ObjectBackend


class NULL(ObjectBackend):

    def __init__(self):  # pragma: nocover
        pass

    def load(self, uuid, info, back_attrs=None):  # pragma: nocover
        return {}

    def identify(self, dn, params, fixed_rdn=None):  # pragma: nocover
        return False

    def identify_by_uuid(self, uuid, params):  # pragma: nocover
        return False

    def exists(self, misc):  # pragma: nocover
        return False

    def remove(self, uuid, data, params):  # pragma: nocover
        return True

    def retract(self, uuid, data, params):  # pragma: nocover
        pass

    def extend(self, uuid, data, params, foreign_keys, dn=None):  # pragma: nocover
        return None

    def move_extension(self, uuid, new_base):  # pragma: nocover
        pass

    def move(self, uuid, new_base):  # pragma: nocover
        return True

    def create(self, base, data, params, foreign_keys=None):  # pragma: nocover
        return None

    def update(self, uuid, data, params):  # pragma: nocover
        return True

    def is_uniq(self, attr, value, at_type):  # pragma: nocover
        return False

    def query(self, base, scope, params, fixed_rdn=None):  # pragma: nocover
        return []
