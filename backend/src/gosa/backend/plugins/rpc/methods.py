# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import re
import os
import datetime
import shlex
import time
import gosa.backend.objects.renderer
from json import loads, dumps
from zope.interface import implementer
from gosa.common import Environment
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.utils import N_
from gosa.common.components import PluginRegistry
from gosa.common.components.jsonrpc_utils import Binary
from gosa.backend.objects import ObjectProxy
from gosa.backend.objects.factory import ObjectFactory
from gosa.common.handler import IInterfaceHandler
from gosa.common.error import GosaErrorHandler as C
from gosa.backend.objects.index import ObjectInfoIndex, KeyValueIndex
from sqlalchemy import and_, or_, func


# Register the errors handled  by us
C.register_codes(dict(
    INVALID_SEARCH_SCOPE=N_("Invalid scope '%(scope)s' [SUB, BASE, ONE, CHILDREN]"),
    INVALID_SEARCH_DATE=N_("Invalid date specification '%(date)s' [hour, day, week, month, year, all]"),
    UNKNOWN_USER=N_("Unknown user '%(target)s'"),
    BACKEND_PARAMETER_MISSING=N_("Backend parameter for '%(extension)s.%(attribute)s' is missing")))


class GOsaException(Exception):
    pass


@implementer(IInterfaceHandler)
class RPCMethods(Plugin):
    """
    Key for configuration section **gosa**

    +------------------+------------+-------------------------------------------------------------+
    + Key              | Format     +  Description                                                |
    +==================+============+=============================================================+
    + cache-path       | String     + Path where the GOsa module will hook in it's cache          |
    +                  |            + path to the web space.                                      |
    +------------------+------------+-------------------------------------------------------------+

    """
    _target_ = 'gui'
    _priority_ = 80
    __value_extender = None
    __search_aid = None

    def __init__(self):
        self.env = Environment.getInstance()

        # Load container mapping from object Factory
        factory = ObjectFactory.getInstance()
        self.containers = []
        for ot, info in factory.getObjectTypes().items():
            if 'container' in info:
                self.containers.append(ot)

    def serve(self):
        # Collect value extenders
        self.__value_extender = gosa.backend.objects.renderer.get_renderers()
        self.__search_aid = PluginRegistry.getInstance("ObjectIndex").get_search_aid()
        self.__oi = PluginRegistry.getInstance("ObjectIndex")

        # Load DB session
        self.__session = self.env.getDatabaseSession('backend-database')

    @Command(__help__=N_("Returns a list containing all available object names"))
    def getAvailableObjectNames(self, only_base_objects=False, base=None):
        factory = ObjectFactory.getInstance()
        if base is not None:
            return factory.getAllowedSubElementsForObject(base)
        else:
            return factory.getAvailableObjectNames(only_base_objects, base)

    @Command(needsUser=True, __help__=N_("Returns a list of objects that can be stored as sub-objects for the given object."))
    def getAllowedSubElementsForObject(self, user, base=None):
        factory = ObjectFactory.getInstance()
        return factory.getAllowedSubElementsForObject(user, base)

    @Command(__help__=N_("Returns all templates used by the given object type."))
    def getGuiTemplates(self, objectType):
        factory = ObjectFactory.getInstance()
        if objectType not in factory.getObjectTypes():
            raise GOsaException(C.make_error("OBJECT_UNKNOWN_TYPE", type=objectType))

        return factory.getObjectTemplates(objectType)

    @Command(__help__=N_("Returns all dialog-templates used by the given object type."))
    def getGuiDialogs(self, objectType):
        factory = ObjectFactory.getInstance()
        if objectType not in factory.getObjectTypes():
            raise GOsaException(C.make_error("OBJECT_UNKNOWN_TYPE", type=objectType))

        return factory.getObjectDialogs(objectType)

    @Command(__help__=N_("Get all translations bound to templates."))
    def getTemplateI18N(self, language):
        templates = []
        factory = ObjectFactory.getInstance()

        for otype in factory.getObjectTypes():
            templates += factory.getObjectTemplateNames(otype)

        return factory.getNamedI18N(list(set(templates)), language=language)

    @Command(__help__=N_("Returns details about the currently logged in user"), needsUser=True)
    def getUserDetails(self, userid):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'User', 'uid': userid}, {'sn': 1, 'givenName': 1, 'cn': 1, 'dn': 1, '_uuid': 1})
        if len(res) == 0:
            raise GOsaException(C.make_error("UNKNOWN_USER", target=userid))

        return({'sn': res[0]['sn'][0],
                'givenName': res[0]['givenName'][0],
                'dn': res[0]['dn'],
                'uuid': res[0]['_uuid'],
                'cn': res[0]['cn'][0]})

    @Command(__help__=N_("Checks whether the given extension is already activated for the current object"), needsUser=True)
    def extensionExists(self, userid, dn, etype):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'User', 'dn': dn}, {'_extensions': 1})
        if len(res) == 0:
            raise GOsaException(C.make_error("UNKNOWN_USER", target=userid))
        return etype in res[0]['_extensions'] if '_extensions' in res[0] else False

    @Command(__help__=N_("Save user preferences"), needsUser=True)
    def saveUserPreferences(self, userid, name, value):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'User', 'uid': userid}, {'dn': 1})
        if len(res) == 0:
            raise GOsaException(C.make_error("UNKNOWN_USER", target=userid))

        user = ObjectProxy(res[0]['dn'])
        prefs = user.guiPreferences

        if not prefs:
            prefs = {}
        else:
            prefs = loads(prefs)

        prefs[name] = value
        user.guiPreferences = dumps(prefs)
        user.commit()

        return True

    @Command(__help__=N_("Load user preferences"))
    def loadUserPreferences(self, userid, name):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'User', 'uid': userid}, {'dn': 1})
        if len(res) == 0:
            raise GOsaException(C.make_error("UNKNOWN_USER", target=userid))

        user = ObjectProxy(res[0]['dn'])
        prefs = user.guiPreferences

        if not prefs:
            prefs = {}
        else:
            prefs = loads(prefs)

        if name in prefs:
            return prefs[name]

        return None

    @Command(needsUser=True, __help__=N_("Search for object information"))
    def searchForObjectDetails(self, user, extension, attribute, fltr, attributes, skip_values):
        """
        Search selectable items valid for the attribute "extension.attribute".

        This is used to add new groups to the users groupMembership attribute.
        """

        # Extract the the required information about the object
        # relation out of the BackendParameters for the given extension.
        of = ObjectFactory.getInstance()
        be_data = of.getObjectBackendParameters(extension, attribute)
        if not be_data:
            raise GOsaException(C.make_error("BACKEND_PARAMETER_MISSING", extension=extension, attribute=attribute))

        # Collection basic information
        otype, oattr, foreignMatchAttr, matchAttr = be_data[attribute] #@UnusedVariable

        # Create a list of attributes that will be requested
        if oattr not in attributes:
            attributes.append(oattr)
        attrs = dict([(x, 1) for x in attributes])
        if not "dn" in attrs:
            attrs.update({'dn': 1})

        # Start the query and brind the result in a usable form
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({
            'or_': {'_type': otype, '_extensions': otype},
            oattr: '%{}%'.format(fltr) if len(fltr) > 0 else '%'
            }, attrs)
        result = []

        # Do we have read permissions for the requested attribute
        env = Environment.getInstance()
        topic = "%s.objects.%s" % (env.domain, otype)
        aclresolver = PluginRegistry.getInstance("ACLResolver")

        for entry in res:

            if not aclresolver.check(user, topic, "s", base=entry['dn']):
                continue

            item = {}
            for attr in attributes:
                if attr in entry and len(entry[attr]):
                    item[attr] = entry[attr] if attr == "dn" else entry[attr][0]
                else:
                    item[attr] = ""
            item['__identifier__'] = item[oattr]

            # Skip values that are in the skip list
            if skip_values and item['__identifier__'] in skip_values:
                continue

            result.append(item)

        return result

    @Command(__help__=N_("Resolves object information"))
    def getObjectDetails(self, extension, attribute, names, attributes):
        """
        This method is used to complete object information shown in the gui.
        e.g. The groupMembership table just knows the groups cn attribute.
             To be able to show the description too, it uses this method.

        #TODO: @fabian - this function is about 95% the same than the one
        #                above.
        """

        # Extract the the required information about the object
        # relation out of the BackendParameters for the given extension.
        of = ObjectFactory.getInstance()
        be_data = of.getObjectBackendParameters(extension, attribute)

        if not be_data:
            raise GOsaException(C.make_error("BACKEND_PARAMETER_MISSING", extension=extension, attribute=attribute))

        # Collection basic information
        otype, oattr, foreignMatchAttr, matchAttr = be_data[attribute] #@UnusedVariable

        # Create a list of attributes that will be requested
        if oattr not in attributes:
            attributes.append(oattr)
        attrs = dict([(x, 1) for x in attributes])

        # Start the query and bring the result in a usable form
        index = PluginRegistry.getInstance("ObjectIndex")

        res = index.search({
            'or_': {'_type': otype, '_extensions': otype, oattr: names}
            }, attrs)

        result = {}
        mapping = {}

        for entry in names:
            _id = len(result)
            mapping[entry] = _id
            result[_id] = None

        for entry in res:
            item = {}
            for attr in attributes:
                if attr in entry and len(entry[attr]):
                    item[attr] = entry[attr] if attr == 'dn' else entry[attr][0]
                else:
                    item[attr] = ""

            if item[oattr] in mapping:
                _id = mapping[item[oattr]]
                result[_id] = item

        return {"result": result, "map": mapping}

    @Command(__help__=N_("Returns a list with all selectable samba-domain-names"))
    def getSambaDomainNames(self):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'SambaDomain', 'sambaDomainName': '%'},
            {'sambaDomainName': 1})

        return list(set([x['sambaDomainName'][0] for x in res]))

    @Command(__help__=N_("Returns a list of DOS/Windows drive letters"))
    def getSambaDriveLetters(self):
        return ["%s:" % c for c in self.letterizer('C', 'Z')]

    def letterizer(self, start='A', stop='Z'):
        for number in range(ord(start), ord(stop) + 1):
            yield chr(number)

    @Command(needsUser=True, __help__=N_("Filter for indexed attributes and return the matches."))
    def search(self, user, base, scope, qstring, fltr=None):
        """
        Performs a query based on a simple search string consisting of keywords.

        Query the database using the given query string and an optional filter
        dict - and return the result set.

        ========== ==================
        Parameter  Description
        ========== ==================
        base       Query base
        scope      Query scope (SUB, BASE, ONE, CHILDREN)
        qstring    Query string
        fltr       Hash for extra parameters
        ========== ==================

        ``Return``: List of dicts
        """

        res = {}
        keywords = None
        dn_hook = "_parent_dn"
        fallback = fltr and "fallback" in fltr and fltr["fallback"]

        def keywords_to_query_list(subject, keywords, fallback=False):
            res = []

            for kw in keywords:
                if fallback:
                    if not self.__oi.fuzzy:
                        res.append(or_(
                            func.levenshtein(func.substring(subject, 0, 50), func.substring(kw, 0, 50)) < 3,
                            subject.like("%" + kw.replace(r"%", "\%") + "%")
                        ))
                    else:
                        res.append(subject.like("%" + kw.replace(r"%", "\%") + "%"))
                else:
                    res.append(subject == kw)

            return res

        if not base:
            return []

        # Set defaults
        if not fltr:
            fltr = {}
        if not 'category' in fltr:
            fltr['category'] = "all"
        if not 'secondary' in fltr:
            fltr['secondary'] = "enabled"
        if not 'mod-time' in fltr:
            fltr['mod-time'] = "all"
        if 'adjusted-dn' in fltr and fltr['adjusted-dn'] is True:
            dn_hook = "_adjusted_parent_dn"
        actions = 'actions' in fltr and fltr['actions'] is True

        if qstring:
            try:
                keywords = [s.strip("'").strip('"') for s in shlex.split(qstring)]
            except ValueError:
                keywords = [s.strip("'").strip('"') for s in qstring.split(" ")]
            qstring = qstring.strip("'").strip('"')
            keywords.append(qstring)

            # Make keywords unique
            keywords = list(set(keywords))

        # Sanity checks
        scope = scope.upper()
        if not scope in ["SUB", "BASE", "ONE", "CHILDREN"]:
            raise GOsaException(C.make_error("INVALID_SEARCH_SCOPE", scope=scope))
        if not fltr['mod-time'] in ["hour", "day", "week", "month", "year", "all"]:
            raise GOsaException(C.make_error("INVALID_SEARCH_DATE", date=fltr['mod-time']))

        # Build query: join attributes and keywords
        queries = []
        for typ in self.__search_aid['attrs'].keys():

            # Only filter for cateogry if desired
            if not ("all" == fltr['category'] or typ == fltr['category']):
                continue

            attrs = self.__search_aid['attrs'][typ]

            if len(attrs) == 0:
                continue

            if keywords:

                if len(attrs) == 1:
                    if hasattr(ObjectInfoIndex, attrs[0]):
                        sq = keywords_to_query_list(getattr(ObjectInfoIndex, attrs[0]), keywords, fallback)
                        queries.append(and_(ObjectInfoIndex._type == typ, or_(*sq)))

                    else:
                        sq = keywords_to_query_list(KeyValueIndex.value, keywords, fallback)
                        queries.append(and_(
                            ObjectInfoIndex._type == typ,
                            KeyValueIndex.uuid == ObjectInfoIndex.uuid,
                            KeyValueIndex.key == attrs[0],
                            or_(*sq)))

                if len(attrs) > 1:
                    cond = []
                    for attr in attrs:
                        if hasattr(ObjectInfoIndex, attr):
                            sq = keywords_to_query_list(getattr(ObjectInfoIndex, attr), keywords, fallback)
                            cond.extend(sq)
                        else:
                            sq = keywords_to_query_list(KeyValueIndex.value, keywords, fallback)
                            cond.append(and_(KeyValueIndex.uuid == ObjectInfoIndex.uuid, KeyValueIndex.key == attr, or_(*sq)))

                    queries.append(and_(ObjectInfoIndex._type == typ, or_(*cond)))

            else:
                if dn_hook != "_adjusted_parent_dn":
                    queries.append(ObjectInfoIndex._type == typ)

        # Build query: assemble
        query = None
        if scope == "SUB":
            if queries:
                query = and_(or_(ObjectInfoIndex._parent_dn == base, ObjectInfoIndex._parent_dn.like("%," + base)), or_(*queries))
            else:
                query = or_(ObjectInfoIndex._parent_dn == base, ObjectInfoIndex._parent_dn.like("%," + base))

        elif scope == "ONE":
            query = and_(or_(ObjectInfoIndex.dn == base, getattr(ObjectInfoIndex, dn_hook) == base), or_(*queries))

        elif scope == "CHILDREN":
            query = and_(getattr(ObjectInfoIndex, dn_hook) == base, or_(*queries))

        else:
            if queries:
                query = and_(ObjectInfoIndex.dn == base, or_(*queries))
            else:
                query = ObjectInfoIndex.dn == base

        # Build query: eventually extend with timing information
        td = None
        if fltr['mod-time'] != "all":
            now = datetime.datetime.now()
            if fltr['mod-time'] == 'hour':
                td = now - datetime.timedelta(hours=1)
            elif fltr['mod-time'] == 'day':
                td = now - datetime.timedelta(days=1)
            elif fltr['mod-time'] == 'week':
                td = now - datetime.timedelta(weeks=1)
            elif fltr['mod-time'] == 'month':
                td = now - datetime.timedelta(days=31)
            elif fltr['mod-time'] == 'year':
                td = now - datetime.timedelta(days=365)

            query = and_(ObjectInfoIndex._last_modified >= td, query)

        # Perform primary query and get collect the results
        squery = []
        these = dict([(x, 1) for x in self.__search_aid['used_attrs']])
        these.update(dict(dn=1, _type=1, _uuid=1, _last_changed=1))
        these = list(these.keys())

        for item in self.__session.query(ObjectInfoIndex).filter(query):
            self.__update_res(res, item, user, self.__make_relevance(item, keywords, fltr), these=these, actions=actions)

            # Collect information for secondary search?
            if fltr['secondary'] != "enabled":
                continue

            kv = self.__index_props_to_key_value(item.properties)
            if item._type in self.__search_aid['resolve']:
                for r in self.__search_aid['resolve'][item._type]:
                    if r['attribute'] in kv:
                        tag = r['type'] if r['type'] else item._type

                        # If a category was choosen and it does not fit the
                        # desired target tag - skip that one
                        if not (fltr['category'] == "all" or fltr['category'] == tag):
                            continue

                        if hasattr(ObjectInfoIndex, r['filter']):
                            squery.append(and_(ObjectInfoIndex._type == tag, getattr(ObjectInfoIndex, r['filter']) == kv[r['attribute']]))
                        else:
                            squery.append(and_(ObjectInfoIndex._type == tag, KeyValueIndex.key == r['filter'], KeyValueIndex.value == kv[r['attribute']][0]))

        # Perform secondary query and update the result
        if fltr['secondary'] == "enabled" and squery:
            query = or_(*squery)

            # Add "_last_changed" information to query
            if fltr['mod-time'] != "all":
                query = and_(query, ObjectInfoIndex._last_modified >= td)

            # Execute query and update results
            for item in self.__session.query(ObjectInfoIndex).filter(query):
                self.__update_res(res, item, user, self.__make_relevance(item, keywords, fltr, True), secondary=True, these=these, actions=actions)

        return list(res.values())

    def __make_relevance(self, item, keywords, fltr, fuzzy=False):
        """
        Very simple relevance weight-o-meter for search results. To
        be improved...

        It basically takes the item and checks if one of the keyword
        is contained. Takes account on fuzzyness, secondary searches,
        tags.
        """
        penalty = 1

        # Prepare attribute set
        values = []
        for prop in item.properties:
            values.append(prop.value)

        # Walk thru keywords
        if keywords:
            for keyword in keywords:

                # No exact match
                if not keyword in values:
                    penalty *= 2

                # Penalty for not having an case insensitive match
                elif not keyword.lower() in [s.value.lower() for s in item.properties]:
                    penalty *= 4

                # Penalty for not having the correct category
                elif fltr['category'] != "all" and fltr['category'].lower() != item['_type'].lower():
                    penalty *= 2

            # Penalty for not having category in keywords
            if item._type in self.__search_aid['aliases']:
                if not set([t.lower() for t in self.__search_aid['aliases'][item._type]]).intersection(set([k.lower() for k in keywords])):
                    penalty *= 6

        # Penalty for secondary
        if fltr['secondary'] == "enabled":
            penalty *= 10

        # Penalty for fuzzyness
        if fuzzy:
            penalty *= 10

        return penalty

    def __update_res(self, res, item, user=None, relevance=0, secondary=False, these=None, actions=False):
    
        # Filter out what the current use is not allowed to see
        item = self.__filter_entry(user, item, these)
        if not item or item['dn'] is None:
            # We've obviously no permission to see thins one - skip it
            return

        if item['dn'] in res:
            dn = item['dn']
            if res[dn]['relevance'] > relevance:
                res[dn]['relevance'] = relevance
            return

        entry = {'tag': item['_type'], 'relevance': relevance, 'uuid': item['_uuid'],
            'secondary': secondary, 'lastChanged': item['_last_changed'], 'hasChildren': True}
        for k, v in self.__search_aid['mapping'][item['_type']].items():
            if k:
                if v in item and item[v]:
                    if v == "dn":
                        entry[k] = item[v]
                    else:
                        entry[k] = item[v][0]
                else:
                    entry[k] = self.__build_value(v, item)

            entry['container'] = item['_type'] in self.containers

        if actions and user:
            aclresolver = PluginRegistry.getInstance("ACLResolver")
            topic = "%s.objects.%s" % (self.env.domain, item['_type'])
            entry['actions'] = aclresolver.getAllowedActions(user, topic, base=item['dn'])

        res[item['dn']] = entry

    def __build_value(self, v, info):
        """
        Fill placeholders in the value to be displayed as "description".
        """

        if not v:
            return ""

        # Find all placeholders
        attrs = {}
        for attr in re.findall(r"%\(([^)]+)\)s", v):

            # Extract ordinary attributes
            if attr in info:
                attrs[attr] = ", ".join(info[attr])

            # Check for result renderers
            elif attr in self.__value_extender:
                attrs[attr] = self.__value_extender[attr](info)

            # Fallback - just set nothing
            else:
                attrs[attr] = ""

        # Assemble and remove empty lines and multiple whitespaces
        res = v % attrs
        res = re.sub(r"(<br>)+", "<br>", res)
        res = re.sub(r"^<br>", "", res)
        res = re.sub(r"<br>$", "", res)
        return "<br>".join([s.strip() for s in res.split("<br>")])

    def __filter_entry(self, user, entry, these=None):
        """
        Takes a query entry and decides based on the user what to do
        with the result set.

        ========== ===========================
        Parameter  Description
        ========== ===========================
        user       User ID
        entry      Search entry as hash
        ========== ===========================

        ``Return``: Filtered result entry
        """
        ne = {'dn': entry.dn, '_type': entry._type, '_uuid': entry.uuid, '_last_changed': entry._last_modified}

        if not entry._type in self.__search_aid['mapping']:
            return None

        attrs = self.__search_aid['mapping'][entry._type].values()

        for attr in attrs:
            if attr is not None and these is not None and attr not in these:
                continue

            if attr is not None and self.__has_access_to(user, entry.dn, entry._type, attr):
                if hasattr(ObjectInfoIndex, attr):
                    ne[attr] = getattr(entry, attr)
                else:
                    kv = self.__index_props_to_key_value(entry.properties)

                    ne[attr] = kv[attr] if attr in kv else None
            else:
                ne[attr] = None

        return ne

    def __index_props_to_key_value(self, properties):
        kv = {}

        for prop in properties:
            if not prop.key in kv:
                kv[prop.key] = []

            kv[prop.key].append(prop.value)

        return kv

    def __has_access_to(self, user, object_dn, object_type, attr):
        """
        Checks whether the given user has access to the given object/attribute or not.
        """
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if user:
            topic = "%s.objects.%s.attributes.%s" % (self.env.domain, object_type, attr)
            return aclresolver.check(user, topic, "r", base=object_dn)
        else:
            return True
