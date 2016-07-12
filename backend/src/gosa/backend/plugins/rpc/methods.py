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
from zope.interface import implementer
from gosa.common import Environment
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.utils import N_
from gosa.common.components import PluginRegistry
from gosa.common.components.jsonrpc_utils import Binary
from gosa.backend.objects import ObjectProxy
from gosa.backend.objects.factory import ObjectFactory
import gosa.backend.objects.renderer
from gosa.common.handler import IInterfaceHandler
from json import loads, dumps
from gosa.common.error import GosaErrorHandler as C


# Register the errors handled  by us
C.register_codes(dict(
    INVALID_SEARCH_SCOPE=N_("Invalid scope '%(scope)s' [SUB, BASE, ONE, CHILDREN]"),
    INVALID_SEARCH_DATE=N_("Invalid date specification '%(date)s' [hour, day, week, month, year, all]"),
    UNKNOWN_USER=N_("Unknown user '%(topic)s'"),
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

        # Load DB session
        self.__session = self.env.getDatabaseSession('backend-database')

    @Command(__help__=N_("Returns a list containing all available object names"))
    def getAvailableObjectNames(self):
        factory = ObjectFactory.getInstance()
        return factory.getAvailableObjectNames()

    @Command(__help__=N_("Returns all templates used by the given object type."))
    def getGuiTemplates(self, objectType, theme="default"):
        factory = ObjectFactory.getInstance()
        if objectType not in factory.getObjectTypes():
            raise GOsaException(C.make_error("OBJECT_UNKNOWN_TYPE", type=objectType))

        return factory.getObjectTemplates(objectType, theme)

    @Command(__help__=N_("Returns all dialog-templates used by the given object type."))
    def getGuiDialogs(self, objectType, theme="default"):
        factory = ObjectFactory.getInstance()
        if objectType not in factory.getObjectTypes():
            raise GOsaException(C.make_error("OBJECT_UNKNOWN_TYPE", type=objectType))

        return factory.getObjectDialogs(objectType, theme)

    @Command(__help__=N_("Get all translations bound to templates."))
    def getTemplateI18N(self, language, theme="default"):
        templates = []
        factory = ObjectFactory.getInstance()

        for otype in factory.getObjectTypes():
            templates += factory.getObjectTemplateNames(otype)

        return factory.getNamedI18N(list(set(templates)), language=language, theme=theme)

    @Command(__help__=N_("Returns details about the currently logged in user"), needsUser=True)
    def getUserDetails(self, userid):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'User', 'uid': userid}, {'sn': 1, 'givenName': 1, 'cn': 1, 'dn': 1, '_uuid': 1})
        if len(res) == 0:
            raise GOsaException(C.make_error("UNKNOWN_USER", userid))

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
            raise GOsaException(C.make_error("UNKNOWN_USER", userid))
        print(res[0])
        return etype in res[0]['_extensions'] if '_extensions' in res[0] else False

    @Command(__help__=N_("Save user preferences"), needsUser=True)
    def saveUserPreferences(self, userid, name, value):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'User', 'uid': userid}, {'dn': 1})
        if len(res) == 0:
            raise GOsaException(C.make_error("UNKNOWN_USER", userid))

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
            raise GOsaException(C.make_error("UNKNOWN_USER", userid))

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

        # Start the query and brind the result in a usable form
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
        if 'adjusted-dn' in fltr and fltr['adjusted-dn'] == True:
            dn_hook = "_adjusted_parent_dn"

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

        # Build query: assemble keywords
        _s = {}
        if keywords:
            if fallback:
                _s = {'or_': ["%%s%" % kw for kw in keywords]}
            else:
                _s = {'or_': keywords}

        # Build query: join attributes and keywords
        queries = []
        for typ in self.__search_aid['attrs'].keys():

            # Only filter for cateogry if desired
            if not ("all" == fltr['category'] or typ == fltr['category']):
                continue

            attrs = self.__search_aid['attrs'][typ]

            if len(attrs) == 0:
                continue
            if _s:
                if len(attrs) == 1:
                    queries.append({'_type': typ, attrs[0]: _s})
                if len(attrs) > 1:
                    queries.append({'_type': typ, "or_": list(map(lambda a: {a: _s}, attrs))})
            else:
                if dn_hook != "_adjusted_parent_dn":
                    queries.append({'_type': typ})

        # Build query: assemble
        query = ""
        if scope == "SUB":
            if queries:
                query = {"or_": {"_parent_dn": base, "_parent_dn": "%," + base}, "or_": queries}
            else:
                query = {"or_": {"_parent_dn": base, "_parent_dn": "%," + base}}

        elif scope == "ONE":
            query = {"or_": {"dn": base, dn_hook: base}}
            query.update(dict((k,v) for d in queries for (k,v) in d.items()))

        elif scope == "CHILDREN":
            query = {dn_hook: base}
            query.update(dict((k,v) for d in queries for (k,v) in d.items()))

        else:
            if queries:
                query = {"dn": base, "or_": queries}
            else:
                query = {"dn": base}

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

            td = {">=": time.mktime(td.timetuple())}
            query["_last_changed"] = td

        # Perform primary query and get collect the results
        squery = []
        these = dict([(x, 1) for x in self.__search_aid['used_attrs']])
        these.update(dict(dn=1, _type=1, _uuid=1, _last_changed=1))

        for item in self.db.index.find(query, these):

            self.__update_res(res, item, user, self.__make_relevance(item, keywords, fltr))

            # Collect information for secondary search?
            if fltr['secondary'] != "enabled":
                continue

            if item['_type'] in self.__search_aid['resolve']:
                for r in self.__search_aid['resolve'][item['_type']]:
                    if r['attribute'] in item:
                        tag = r['_type'] if r['_type'] else item['_type']

                        # If a category was choosen and it does not fit the
                        # desired target tag - skip that one
                        if not (fltr['category'] == "all" or fltr['category'] == tag):
                            continue

                        squery.append({'_type': tag, r['filter']: [item[r['attribute']]]})

        # Perform secondary query and update the result
        if fltr['secondary'] == "enabled" and squery:
            query = {"or_": squery}

            # Add "_last_changed" information to query
            if fltr['mod-time'] != "all":
                query["_last_changed"] = td

            # Execute query and update results
            for item in self.db.index.find(query, these):
                self.__update_res(res, item, user, self.__make_relevance(item, keywords, fltr, True), secondary=True)

        return res.values()

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
        for attrs in item.values():
            if isinstance(attrs, list):
                for attr in attrs:
                    if isinstance(attr, str) and not isinstance(attr, Binary):
                        values.append(attr)
        # Walk thru keywords
        if keywords:
            for keyword in keywords:

                # No exact match
                if not keyword in values:
                    penalty *= 2

                # Penalty for not having an case insensitive match
                elif not keyword.lower() in [s.lower() for s in item]:
                    penalty *= 4

                # Penalty for not having the correct category
                elif fltr['category'] != "all" and fltr['category'].lower() != item['_type'].lower():
                    penalty *= 2

            # Penalty for not having category in keywords
            if item['_type'] in self.__search_aid['aliases']:
                if not set([t.lower() for t in self.__search_aid['aliases'][item['_type']]]).intersection(set([k.lower() for k in keywords])):
                    penalty *= 6

        # Penalty for secondary
        if fltr['secondary'] == "enabled":
            penalty *= 10

        # Penalty for fuzzyness
        if fuzzy:
            penalty *= 10

        return penalty

    def __update_res(self, res, item, user=None, relevance=0, secondary=False):
    
        # Filter out what the current use is not allowed to see
        item = self.__filter_entry(user, item)
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
                if k == "icon":
                    continue
                if v in item and item[v]:
                    if v == "dn":
                        entry[k] = item[v]
                    else:
                        entry[k] = item[v][0]
                else:
                    entry[k] = self.__build_value(v, item)
    
            entry['icon'] = None
            entry['container'] = item['_type'] in self.containers
    
            icon_attribute = self.__search_aid['mapping'][item['_type']]['icon']
            if icon_attribute and icon_attribute in item and item[icon_attribute]:
                cache_path = self.env.config.get('gui.cache-path', default="/cache")
                entry['icon'] = os.path.join(cache_path, item['_uuid'],
                        icon_attribute, "0", "64.jpg?c=%s" %
                        item['_last_changed'])
    
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
    
    def __filter_entry(self, user, entry):
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
        ne = {'dn': entry['dn'], '_type': entry['_type'], '_uuid':
                entry['_uuid'], '_last_changed': entry['_last_changed']}
    
        if not entry['_type'] in self.__search_aid['mapping']:
            return None
    
        attrs = self.__search_aid['mapping'][entry['_type']].values()
    
        for attr in attrs:
            if attr is not None and self.__has_access_to(user, entry['dn'], entry['_type'], attr):
                ne[attr] = entry[attr] if attr in entry else None
            else:
                ne[attr] = None
    
        return ne
    
    def __has_access_to(self, user, object_dn, object_type, attr):
        """
        Checks whether the given user has access to the given object/attribute or not.
        """
        #aclresolver = PluginRegistry.getInstance("ACLResolver")
        #if user:
        #    topic = "%s.objects.%s.attributes.%s" % (self.env.domain, object_type, attr)
        #    return aclresolver.check(user, topic, "r", base=object_dn)
        #else:
        #    return True
        print("!ACL check disabled")
        return True
