# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

__import__('pkg_resources').declare_namespace(__name__)
import ldap
from itertools import permutations
from gosa.common.utils import N_
from gosa.common.error import GosaErrorHandler as C
from gosa.backend.exceptions import DNGeneratorError


# Register the errors handled  by us
C.register_codes(dict(
    GENERATOR_RDN_ATTRIBUTE_MISSING=N_("Attribute '%(topic)s' needed to generate a RDN is missing"),
    RDN_NOT_SPECIFIED=N_("No 'RDN' backend parameter specified"),
    NO_UNIQUE_DN=N_("Cannot generate a unique DN in '%(base)s' using a combination of %(rdns)s"),
    TARGET_EXISTS=N_("Target DN '%(target)s' already exists"),
    DB_CONFIG_MISSING=N_("No database configuration found for '%(target)s'"),
    BACKEND_ATTRIBUTE_CONFIG_MISSING=N_("Attribute '%s' uses the ObjectHandler backend but there is no config for it"),
    SOURCE_OBJECT_NOT_FOUND=N_("Cannot find source object '%(object)s'"),
    NO_UNIQUE_ENTRY=N_("No unique '%(object)s' object which matches '%(attribute)s == %(value)s'"),
    ID_GENERATION_FAILED=N_("Failed to generate a unique ID"),
    ENTRY_UUID_NOT_FOUND=N_("Entry '%(uuid)s' not found"),
    ENTRY_UUID_NOT_UNIQUE=N_("Entry '%(uuid)s' not unique"),
    ))

"""
Shared backend attributes:
--------------------------

* `_uuidAttribute`: change the attribute where the uuid is stored to identify the object in the backend
                    (default is uuid, but e.g. the foreman backend needs another ID for the foremanHostGroup)

"""
class ObjectBackend(object):

    def dn2uuid(self, dn):  # pragma: nocover
        """
        Convert DN to uuid.
        """
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", dn, method="dn2uuid"))

    def uuid2dn(self, uuid):  # pragma: nocover
        """
        Convert uuid to DN.
        """
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", uuid, method="uuid2dn"))

    def get_timestamps(self, dn):  # pragma: nocover
        """
        Return a tuple (createdTimestamp, modifyTimestamp)
        """
        return None, None

    def load(self, uuid, keys, back_attrs=None, needed=None):  # pragma: nocover
        """
        Load given keys from entry with uuid.
        """
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", uuid, method="load"))

    def process_data(self, data, backend_props):
        """ Process incoming data to return a key/value dict as returney by the load method """
        res = {}
        # attach requested attributes to result set
        for attr, type in data.items():
            if attr in data and data[attr] is not None and attr in backend_props:
                res[attr] = [data[attr]]

        return res

    def move(self, uuid, new_base):  # pragma: nocover
        """
        Move object to new base.
        """
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", uuid, method="move"))

    def move_extension(self, uuid, new_base):  # pragma: nocover
        """
        Notify extension that it is on another base now.
        """
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", uuid, method="move_extension"))

    def create(self, dn, data, params, needed=None):  # pragma: nocover
        """
        Create a new base object entry with the given DN.
        """
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", dn, method="create"))

    def extend(self, uuid, data, params, foreign_keys, dn=None, needed=None):  # pragma: nocover
        """
        Create an extension to a base object with the given UUID.
        """
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", uuid, method="extend"))

    def update(self, uuid, data, params, needed=None):  # pragma: nocover
        """
        Update a base entry or an extension with the given UUID.
        """
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", uuid, method="update"))

    def exists(self, misc, needed=None):  # pragma: nocover
        """
        Check if an object with the given UUID or DN exists.
        """
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", method="exists"))

    def remove(self, uuid, data, params, needed=None):  # pragma: nocover
        """
        Remove base object specified by UUID.
        """
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", uuid, method="remove"))

    def retract(self, uuid, data, params, needed=None):  # pragma: nocover
        """
        Retract extension from base object specified by UUID.
        """
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", uuid, method="retract"))

    def is_uniq(self, attr, value, at_type):  # pragma: nocover
        """
        Check if the given attribute is unique.
        """
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", method="is_uniq"))

    def identify(self, dn, params, fixed_rdn=None):  # pragma: nocover
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", dn, method="identify"))

    def identify_by_uuid(self, dn, params):  # pragma: nocover
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", dn, method="identify_by_uuid"))

    def query(self, base, scope, params, fixed_rdn=None):  # pragma: nocover
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", method="query"))

    def get_next_id(self, attr):  # pragma: nocover
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", method="get_next_id"))

    def build_dn_list(self, rdns, base, data, FixedRDN):
        """
        Build a list of possible DNs for the given properties
        """

        fix = rdns[0]
        var = rdns[1:] if len(rdns) > 1 else []
        dns = [fix]

        # Check if we've have to use a fixed RDN.
        if FixedRDN:
            return["%s,%s" % (FixedRDN, base)]

        # Bail out if fix part is not in data
        if not fix in data:
            raise DNGeneratorError(C.make_error("GENERATOR_RDN_ATTRIBUTE_MISSING", fix))

        # Append possible variations of RDN attributes
        if var:
            for rdn in permutations(var + [None] * (len(var) - 1), len(var)):
                dns.append("%s,%s" % (fix, ",".join(filter(lambda x: x and x in data and data[x], list(rdn)))))
        dns = list(set(dns))

        # Assemble DN of RDN combinations
        dn_list = []
        for t in [tuple(d.split(",")) for d in dns]:
            ndn = []
            for k in t:
                ndn.append("%s=%s" % (k, ldap.dn.escape_dn_chars(data[k]['value'][0])))
            dn_list.append("+".join(ndn) + "," + base)

        return sorted(dn_list, key=len)
