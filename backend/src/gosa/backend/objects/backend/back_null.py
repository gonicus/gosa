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

    def __init__(self):
        pass

    def load(self, uuid, info, back_attrs=None):
        return {}

    def identify(self, dn, params, fixed_rdn=None):
        return False

    def identify_by_uuid(self, uuid, params):
        return False

    def exists(self, misc):
        return False

    def remove(self, uuid, data, params):
        return True

    def retract(self, uuid, data, params):
        pass

    def extend(self, uuid, data, params, foreign_keys):
        return None

    def move_extension(self, uuid, new_base):
        pass

    def move(self, uuid, new_base):
        return True

    def create(self, base, data, params, foreign_keys=None):
        return None

    def update(self, uuid, data, params):
        return True

    def is_uniq(self, attr, value):
        return False

    def query(self, base, scope, params, fixed_rdn=None):
        return []
