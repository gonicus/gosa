# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import ldap #@UnusedImport
import ldap.dn
import ldap.filter
import time
import datetime
from itertools import permutations
from logging import getLogger
from gosa.common import Environment
from gosa.common.utils import is_uuid, N_
from gosa.common.components.jsonrpc_utils import Binary
from gosa.common.error import GosaErrorHandler as C
from gosa.backend.utils.ldap import LDAPHandler
from gosa.backend.objects.backend import ObjectBackend
from gosa.backend.exceptions import EntryNotFound, RDNNotSpecified, DNGeneratorError


# Register the errors handled  by us
C.register_codes(dict(
    NO_POOL_ID=N_("No ID pool found"),
    MULTIPLE_ID_POOLS=N_("Multiple ID pools found")
    ))


class LDAP(ObjectBackend):

    def __init__(self):
        # Load LDAP handler class
        self.env = Environment.getInstance()
        self.log = getLogger(__name__)

        self.lh = LDAPHandler.get_instance()
        self.con = self.lh.get_connection()
        self.uuid_entry = self.env.config.get("backend-ldap.uuid-attribute", "entryUUID")
        self.create_ts_entry = self.env.config.get("backend-ldap.create-attribute", "createTimestamp")
        self.modify_ts_entry = self.env.config.get("backend-ldap.modify-attribute", "modifyTimestamp")

        # Internal identify cache
        self.__i_cache = {}
        self.__i_cache_ttl = {}

    def __del__(self):
        self.lh.free_connection(self.con)

    def load(self, uuid, info, back_attrs=None):
        keys = info.keys()
        fltr_tpl = "%s=%%s" % self.uuid_entry
        fltr = ldap.filter.filter_format(fltr_tpl, [uuid])

        self.log.debug("searching with filter '%s' on base '%s'" % (fltr,
            self.lh.get_base(False)))
        res = self.con.search_s(self.lh.get_base(False), ldap.SCOPE_SUBTREE, fltr,
            keys)

        # Check if res is valid
        self.__check_res(uuid, res)

        # Do value conversation
        items = dict((k, v) for k, v in res[0][1].iteritems() if k in keys)
        for key in items.keys():
            cnv = getattr(self, "_convert_from_%s" % info[key].lower())
            lcnv = []
            for lvalue in items[key]:
                lcnv.append(cnv(lvalue))
            items[key] = lcnv
        return items

    def identify_by_uuid(self, uuid, params):
        return False

    def identify(self, dn, params, fixed_rdn=None):

        # Check for special RDN attribute
        if 'RDN' in params:
            rdns = [o.strip() for o in params['RDN'].split(",")]
            rdn_parts = ldap.dn.str2dn(dn.encode('utf-8'), flags=ldap.DN_FORMAT_LDAPV3)[0]

            found = False
            for rdn_a, rdn_v, dummy in rdn_parts: #@UnusedVariable
                if rdn_a in rdns:
                    found = True

            if not found:
                return False

        custom_filter = ""
        if 'filter' in params:
            custom_filter = params['filter']

        ocs = [o.strip() for o in params['objectClasses'].split(",")]

        # Remove cache if too old
        if dn in self.__i_cache_ttl and self.__i_cache_ttl[dn] - time.time() > 60:
            del self.__i_cache[dn]
            del self.__i_cache_ttl[dn]

        # Split for fixed attrs
        fixed_rdn_filter = ""
        attr = None
        if fixed_rdn:
            attr, value, _ = ldap.dn.str2dn(fixed_rdn.encode('utf-8'), flags=ldap.DN_FORMAT_LDAPV3)[0][0]
            fixed_rdn_filter = ldap.filter.filter_format("(%s=*)", [attr])

        # If we just query for an objectClass, try to get the
        # answer from the cache.
        if not 'filter' in params and dn in self.__i_cache:

            if fixed_rdn:
                if dn in self.__i_cache and attr in self.__i_cache[dn]:
                    self.__i_cache_ttl[dn] = time.time()
                    #noinspection PyUnboundLocalVariable
                    return len(set(ocs) - set(self.__i_cache[dn]['objectClass'])) == 0 and len({value} - set(self.__i_cache[dn][attr])) == 0

            else:
                self.__i_cache_ttl[dn] = time.time()
                return len(set(ocs) - set(self.__i_cache[dn]['objectClass'])) == 0

        fltr = "(&(objectClass=*)" + fixed_rdn_filter + custom_filter + ")"
        try:
            res = self.con.search_s(dn.encode('utf-8'), ldap.SCOPE_BASE, fltr,
                    [self.uuid_entry, 'objectClass'] + ([attr] if attr else []))
        except ldap.NO_SUCH_OBJECT:
            return False

        if len(res) == 1:
            if not dn in self.__i_cache:
                self.__i_cache[dn] = {}

            self.__i_cache[dn]['objectClass'] = res[0][1]['objectClass']
            self.__i_cache_ttl[dn] = time.time()

            if fixed_rdn:
                if attr in res[0][1]:
                    self.__i_cache[dn][attr] = [x.decode('utf-8') for x in res[0][1][attr]]
                else:
                    self.__i_cache[dn][attr] = []

                #noinspection PyUnboundLocalVariable
                return len(set(ocs) - set(self.__i_cache[dn]['objectClass'])) == 0 and len({value} - set(self.__i_cache[dn][attr])) == 0
            else:
                return len(set(ocs) - set(self.__i_cache[dn]['objectClass'])) == 0

        return False

    def query(self, base, scope, params, fixed_rdn=None):
        ocs = ["(objectClass=%s)" % o.strip() for o in params['objectClasses'].split(",")]
        fltr = "(&" + "".join(ocs) + (ldap.filter.filter_format("(%s)", [fixed_rdn]) if fixed_rdn else "") + ")"
        res = self.con.search_s(base.encode('utf-8'), ldap.SCOPE_ONELEVEL, fltr,
                [self.uuid_entry])
        return [unicode(x.decode('utf-8')) for x in dict(res).keys()]

    def exists(self, misc):
        if is_uuid(misc):
            fltr_tpl = "%s=%%s" % self.uuid_entry
            fltr = ldap.filter.filter_format(fltr_tpl, [misc])

            res = self.con.search_s(self.lh.get_base(False), ldap.SCOPE_SUBTREE,
                    fltr, [self.uuid_entry])

        else:
            res = self.con.search_s(misc, ldap.SCOPE_ONELEVEL, '(objectClass=*)',
                [self.uuid_entry])

        if not res:
            return False

        return len(res) == 1

    def remove(self, uuid, data, params):
        dn = self.uuid2dn(uuid)

        self.log.debug("removing entry '%s'" % dn)
        return self.con.delete_s(dn.encode('utf-8'))

    def __delete_children(self, dn):
        res = self.con.search_s(dn, ldap.SCOPE_ONELEVEL, '(objectClass=*)',
                [self.uuid_entry])

        for c_dn in res.keys():
            self.__delete_children(c_dn)

        # Delete ourselves
        self.log.debug("removing entry '%s'" % dn)
        return self.con.delete_s(dn)

    def retract(self, uuid, data, params):
        # Remove defined data from the specified object
        dn = self.uuid2dn(uuid)
        mod_attrs = []

        # We know about object classes - remove them
        if 'objectClasses' in params:
            ocs = [o.strip() for o in params['objectClasses'].split(",")]
            mod_attrs.append((ldap.MOD_DELETE, 'objectClass', ocs))

        # Remove all other keys related to this object
        for key in data.keys():
            mod_attrs.append((ldap.MOD_DELETE, key, None))

        self.con.modify_s(dn.encode('utf-8'), mod_attrs)

        # Clear identify cache, else we will receive old values from self.identifyObject
        if dn in self.__i_cache_ttl:
            del self.__i_cache[dn]
            del self.__i_cache_ttl[dn]

    def extend(self, uuid, data, params, foreign_keys):
        dn = self.uuid2dn(uuid)
        return self.create(dn, data, params, foreign_keys)

    def move_extension(self, uuid, new_base):
        # There is no need to handle this inside of the LDAP backend
        pass

    def move(self, uuid, new_base):
        dn = self.uuid2dn(uuid)
        self.log.debug("moving entry '%s' to new base '%s'" % (dn, new_base))
        rdn = ldap.dn.explode_dn(dn, flags=ldap.DN_FORMAT_LDAPV3)[0]
        return self.con.rename_s(dn, rdn, new_base)

    def create(self, base, data, params, foreign_keys=None):
        mod_attrs = []
        self.log.debug("gathering modifications for entry on base '%s'" % base)
        for attr, entry in data.iteritems():

            # Skip foreign keys
            if foreign_keys and attr in foreign_keys:
                continue

            cnv = getattr(self, "_convert_to_%s" % entry['type'].lower())
            items = []
            for lvalue in entry['value']:
                items.append(cnv(lvalue))

            self.log.debug(" * add attribute '%s' with value %s" % (attr, items))
            if foreign_keys is None:
                mod_attrs.append((attr, items))
            else:
                mod_attrs.append((ldap.MOD_ADD, attr, items))

        # We know about object classes - add them if possible
        if 'objectClasses' in params:
            ocs = [o.strip() for o in params['objectClasses'].split(",")]
            if foreign_keys is None:
                mod_attrs.append(('objectClass', ocs))
            else:
                mod_attrs.append((ldap.MOD_ADD, 'objectClass', ocs))

        if foreign_keys is None:
            # Check if obligatory information for assembling the DN are
            # provided
            if not 'RDN' in params:
                raise RDNNotSpecified(C.make_error("RDN_NOT_SPECIFIED"))

            # Build unique DN using maybe optional RDN parameters
            rdns = [d.strip() for d in params['RDN'].split(",")]

            FixedRDN = params['FixedRDN'] if 'FixedRDN' in params else None
            dn = self.get_uniq_dn(rdns, base, data, FixedRDN)
            if not dn:
                raise DNGeneratorError(C.make_error("NO_UNIQUE_DN", base=base, rdns=", ".join(rdns)))
            dn = dn.encode('utf-8')

        else:
            dn = base

        self.log.debug("evaluated new entry DN to '%s'" % dn)

        # Write...
        self.log.debug("saving entry '%s'" % dn)

        if foreign_keys is None:
            self.con.add_s(dn, mod_attrs)
        else:
            self.con.modify_s(dn, mod_attrs)

        # Clear identify cache, else we will receive old values from self.identifyObject
        if dn in self.__i_cache_ttl:
            del self.__i_cache[dn]
            del self.__i_cache_ttl[dn]

        # Return automatic uuid
        return self.dn2uuid(dn)

    def update(self, uuid, data, params):

        # Assemble a proper modlist
        dn = self.uuid2dn(uuid)

        mod_attrs = []
        self.log.debug("gathering modifications for entry '%s'" % dn)
        for attr, entry in data.iteritems():

            # Value removed?
            if entry['orig'] and not entry['value']:
                self.log.debug(" * remove attribute '%s'" % attr)
                mod_attrs.append((ldap.MOD_DELETE, attr, None))
                continue

            cnv = getattr(self, "_convert_to_%s" % entry['type'].lower())
            items = []
            for lvalue in entry['value']:
                items.append(cnv(lvalue))

            # New value?
            if not entry['orig'] and entry['value']:
                self.log.debug(" * add attribute '%s' with value %s" % (attr, items))
                mod_attrs.append((ldap.MOD_ADD, attr, items))
                continue

            # Ok, modified...
            self.log.debug(" * replace attribute '%s' with value %s" % (attr, items))
            mod_attrs.append((ldap.MOD_REPLACE, attr, items))

        # Did we change one of the RDN attributes?
        new_rdn_parts = []
        rdns = ldap.dn.str2dn(dn.encode('utf-8'), flags=ldap.DN_FORMAT_LDAPV3)
        rdn_parts = rdns[0]

        for attr, value, idx in rdn_parts:
            if attr in data:
                cnv = getattr(self, "_convert_to_%s" % data[attr]['type'].lower())
                new_rdn_parts.append((attr, cnv(data[attr]['value'][0]), 4))
            else:
                new_rdn_parts.append((attr, value, idx))

        # Build new target DN and check if it has changed...
        tdn = ldap.dn.dn2str([new_rdn_parts] + rdns[1:]).decode('utf-8')

        if tdn != dn:
            self.log.debug("entry needs a rename from '%s' to '%s'" % (dn, tdn))
            self.con.rename_s(dn.encode('utf-8'), ldap.dn.dn2str([new_rdn_parts]))

        # Write back...
        self.log.debug("saving entry '%s'" % tdn)
        return self.con.modify_s(tdn.encode('utf-8'), mod_attrs)

    def uuid2dn(self, uuid):
        # Get DN of entry
        fltr_tpl = "%s=%%s" % self.uuid_entry
        fltr = ldap.filter.filter_format(fltr_tpl, [uuid])

        self.log.debug("searching with filter '%s' on base '%s'" % (fltr,
            self.lh.get_base()))
        res = self.con.search_s(self.lh.get_base(False), ldap.SCOPE_SUBTREE, fltr,
                [self.uuid_entry])

        self.__check_res(uuid, res)

        return res[0][0].decode('utf-8')

    def dn2uuid(self, dn):
        try:
            res = self.con.search_s(dn.encode('utf-8'), ldap.SCOPE_BASE, '(objectClass=*)',
                    [self.uuid_entry])
        except:
            return False

        # Check if res is valid
        self.__check_res(dn, res)

        return res[0][1][self.uuid_entry][0]

    def get_timestamps(self, dn):
        res = self.con.search_s(dn.encode('utf-8'), ldap.SCOPE_BASE,
                '(objectClass=*)', [self.create_ts_entry, self.modify_ts_entry])
        cts = self._convert_from_timestamp(res[0][1][self.create_ts_entry][0])
        mts = self._convert_from_timestamp(res[0][1][self.modify_ts_entry][0])

        return cts, mts

    def get_uniq_dn(self, rdns, base, data, FixedRDN):

        for dn in self.build_dn_list(rdns, base, data, FixedRDN):
            try:
                self.con.search_s(dn.encode('utf-8'), ldap.SCOPE_BASE, '(objectClass=*)',
                    [self.uuid_entry])

            except ldap.NO_SUCH_OBJECT:
                return dn

        return None

    def is_uniq(self, attr, value, at_type):
        fltr_tpl = "%s=%%s" % attr

        cnv = getattr(self, "_convert_to_%s" % at_type.lower())
        value = cnv(value)
        fltr = ldap.filter.filter_format(fltr_tpl, [value])

        self.log.debug("uniq test with filter '%s' on base '%s'" % (fltr,
            self.lh.get_base()))
        res = self.con.search_s(self.lh.get_base(False), ldap.SCOPE_SUBTREE, fltr,
            [self.uuid_entry])

        return len(res) == 0

    def build_dn_list(self, rdns, base, data, FixedRDN):
        fix = rdns[0]
        var = rdns[1:] if len(rdns) > 1 else []
        dns = [fix]

        # Check if we've have to use a fixed RDN.
        if FixedRDN:
            return["%s,%s" % (FixedRDN, base)]

        # Bail out if fix part is not in data
        if not fix in data:
            raise DNGeneratorError(C.make_error("ATTRIBUTE_NOT_FOUND", attribute=fix))

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

    def get_next_id(self, attr):
        fltr = self.env.config.get("backend-ldap.pool-filter", "(objectClass=sambaUnixIdPool)")
        res = self.con.search_s(self.lh.get_base(False), ldap.SCOPE_SUBTREE, fltr, [attr])

        if not res:
            raise EntryNotFound(C.make_error("NO_POOL_ID"))

        if len(res) != 1:
            raise EntryNotFound(C.make_error("MULTIPLE_ID_POOLS"))

        # Current value
        old_value = res[0][1][attr][0]
        new_value = str(int(old_value) + 1)

        # Remove old, add new
        mod_attrs = [
                (ldap.MOD_DELETE, attr, [old_value]),
                (ldap.MOD_ADD, attr, [new_value]),
                ]

        self.con.modify_s(res[0][0], mod_attrs)

        return int(new_value)

    def __check_res(self, uuid, res):
        if not res:
            raise EntryNotFound(C.make_error("ENTRY_UUID_NOT_FOUND", uuid=uuid))

        if len(res) != 1:
            raise EntryNotFound(C.make_error("ENTRY_UUID_NOT_UNIQUE", uuid=uuid))

    def _convert_from_boolean(self, value):
        return value == "TRUE"

    def _convert_from_string(self, value):
        return str(value)

    def _convert_from_unicodestring(self, value):
        return value.decode('utf-8')

    def _convert_from_integer(self, value):
        return int(value)

    def _convert_from_timestamp(self, value):
        return datetime.datetime.strptime(value, "%Y%m%d%H%M%SZ")

    def _convert_from_date(self, value):
        ts = time.mktime(time.strptime(value, "%Y%m%d%H%M%SZ"))
        return datetime.date.fromtimestamp(ts)

    def _convert_from_binary(self, value):
        return Binary(value)

    def _convert_to_boolean(self, value):
        return "TRUE" if value else "FALSE"

    def _convert_to_string(self, value):
        return str(value)

    def _convert_to_unicodestring(self, value):
        return str(value.encode('utf-8'))

    def _convert_to_integer(self, value):
        return str(value)

    def _convert_to_timestamp(self, value):
        return value.strftime("%Y%m%d%H%M%SZ")

    def _convert_to_date(self, value):
        return value.strftime("%Y%m%d%H%M%SZ")

    def _convert_to_binary(self, value):
        return value.get()
