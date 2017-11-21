# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import logging
import re
import os
import datetime
import shlex

import math
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import aliased, joinedload, contains_eager
from sqlalchemy_searchable import search, parse_search_query

import gosa.backend.objects.renderer

from sqlalchemy import desc
from zope.interface import implementer
from gosa.common import Environment
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.utils import N_
from gosa.common.components import PluginRegistry
from gosa.backend.objects import ObjectProxy
from gosa.backend.objects.factory import ObjectFactory
from gosa.common.handler import IInterfaceHandler
from gosa.common.error import GosaErrorHandler as C
from gosa.backend.objects.index import ObjectInfoIndex, KeyValueIndex, SearchObjectIndex
from sqlalchemy import and_, or_, func
from sqlalchemy.inspection import inspect


# Register the errors handled  by us
C.register_codes(dict(
    INVALID_SEARCH_SCOPE=N_("Invalid scope '%(scope)s' [SUB, BASE, ONE, CHILDREN]"),
    INVALID_SEARCH_DATE=N_("Invalid date specification '%(date)s' [hour, day, week, month, year, all]"),
    UNKNOWN_USER=N_("Unknown user '%(target)s'"),
    BACKEND_PARAMETER_MISSING=N_("Backend parameter for '%(extension)s.%(attribute)s' is missing"),
    UNKNOWN_EXTENSION=N_("Unknown extension '%(target)s'")))


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
    __fuzzy_similarity_threshold = 0.3

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        # Load container mapping from object Factory
        factory = ObjectFactory.getInstance()
        self.containers = []
        for ot, info in factory.getObjectTypes().items():
            if 'container' in info:
                self.containers.append(ot)
        self.__fuzzy_similarity_threshold = self.env.config.getfloat("backend.fuzzy-threshold", default=0.3)

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
    def getAllowedSubElementsForObjectWithActions(self, user, base=None):
        factory = ObjectFactory.getInstance()
        return factory.getAllowedSubElementsForObjectWithActions(user, base)

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
        res = index.search({'_type': 'User', 'uid': userid}, {'sn': 1, 'givenName': 1, 'cn': 1, 'dn': 1, '_uuid': 1, '_last_changed': 1})

        if len(res) == 0:
            raise GOsaException(C.make_error("UNKNOWN_USER", target=userid))

        cache_path = self.env.config.get('user.image-path', default="/var/lib/gosa/images")
        icon = "@Ligature/user"
        if os.path.exists(os.path.join(cache_path, res[0]['_uuid'], "jpegPhoto", "0", "64.jpg")):
            icon = "/images/%s/jpegPhoto/0/64.jpg?c=%s" % (res[0]['_uuid'], res[0]["_last_changed"])

        return({'sn': res[0]['sn'][0],
                'givenName': res[0]['givenName'][0],
                'dn': res[0]['dn'],
                'uuid': res[0]['_uuid'],
                'icon': icon,
                'cn': res[0]['cn'][0]})

    @Command(__help__=N_("Checks whether the given extension is already activated for the current object"))
    def extensionExists(self, dn, etype):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'User', 'dn': dn}, {'_extensions': 1})
        if len(res) == 0:
            raise GOsaException(C.make_error("UNKNOWN_EXTENSION", target=etype))
        return etype in res[0]['_extensions'] if '_extensions' in res[0] else False

    @Command(__help__=N_("Save user preferences"), needsUser=True)
    def saveUserPreferences(self, userid, name, value):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'User', 'uid': userid}, {'dn': 1})
        if len(res) == 0:
            raise GOsaException(C.make_error("UNKNOWN_USER", target=userid))

        user = ObjectProxy(res[0]['dn'])
        if user.guiPreferences is None:
            user.guiPreferences = {}

        user.guiPreferences[name] = value
        user.commit()

        return True

    @Command(__help__=N_("Load user preferences"), needsUser=True)
    def loadUserPreferences(self, userid, name):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'User', 'uid': userid}, {'dn': 1})
        if len(res) == 0:
            raise GOsaException(C.make_error("UNKNOWN_USER", target=userid))

        user = ObjectProxy(res[0]['dn'])

        if not user.guiPreferences:
            return None
        elif name in user.guiPreferences:
            return user.guiPreferences[name]
        else:
            return None

    @Command(needsUser=True, __help__=N_("Search for related object information"))
    def searchForObjectDetails(self, user, extension, attribute, search_filter, attributes, skip_values, options=None):
        """
        Search selectable items valid for the attribute "extension.attribute".

        This is used to add new groups to the users groupMembership attribute.
        """

        # Extract the the required information about the object
        # relation out of the BackendParameters for the given extension.
        object_factory = ObjectFactory.getInstance()
        be_data = object_factory.getObjectBackendParameters(extension, attribute)
        if not be_data:
            raise GOsaException(C.make_error("BACKEND_PARAMETER_MISSING", extension=extension, attribute=attribute))

        # Collection basic information
        object_type, object_attribute, _, _ = be_data[attribute]
        return self.searchObjects(user, object_type, object_attribute, search_filter, attributes, skip_values, options)

    @Command(needsUser=True, __help__=N_("Search for object information"))
    def searchObjects(self, user, object_type, object_attribute, search_filter, attributes, skip_values, options=None):

        # Create a list of attributes that will be requested
        if object_attribute is not None and object_attribute not in attributes:
            attributes.append(object_attribute)
        attrs = dict([(x, 1) for x in attributes])
        if "dn" not in attrs:
            attrs.update({'dn': 1})

        # Start the query and format the result
        index = PluginRegistry.getInstance("ObjectIndex")
        query = {}
        object_factory = ObjectFactory.getInstance()
        if object_attribute is not None:
            query[object_attribute] = '%{}%'.format(search_filter) if len(search_filter) > 0 else '%'

        if object_type != "*":
            if object_factory.isBaseType(object_type):
                query["_type"] = object_type
            else:
                query["extension"] = object_type
        if options is not None and 'filter' in options:
            for key, values in options['filter'].items():
                if key not in query:
                    query[key] = values
                else:
                    if isinstance(query[key], list):
                        query[key].append(values)
                    else:
                        query[key] = [query[key]]
                        query[key].append(values)

            del options['filter']

        search_result = index.search(query, attrs, options)

        result = []

        # Do we have read permissions for the requested attribute
        env = Environment.getInstance()
        topic = "%s.objects.%s" % (env.domain, object_type)
        acl_resolver = PluginRegistry.getInstance("ACLResolver")

        for entry in search_result:

            if not acl_resolver.check(user, topic, "s", base=entry['dn']):
                continue

            item = {}
            for attr in attributes:
                if attr in entry and len(entry[attr]):
                    item[attr] = entry[attr] if attr in ["dn", "_type"] else entry[attr][0]
                else:
                    item[attr] = ""
            item['__identifier__'] = item[object_attribute]

            # Skip values that are in the skip list
            if skip_values and item['__identifier__'] in skip_values:
                continue

            result.append(item)

        return result

    @Command(needsUser=True, __help__=N_("Return object information like: title and icon"))
    def getObjectSearchItem(self, user, dn):
        """
        This method returns the search result for one specific object.
        It is used to gain some useful information about the object like title and icon.

        :param dn: string - Object DN
        :return: dict
        """
        # Start the query and bring the result in a usable form
        index = PluginRegistry.getInstance("ObjectIndex")

        item = index.find(user, {'dn': dn})
        if len(item) == 1:
            item = item[0]
        else:
            return None

        if item['_type'] not in self.__search_aid['mapping']:
            return None

        entry = {'tag': item['_type']}
        for k, v in self.__search_aid['mapping'][item['_type']].items():
            if k:
                if v in item and item[v]:
                    if v == "dn":
                        entry[k] = item[v]
                    else:
                        entry[k] = item[v][0]
                else:
                    entry[k] = self.__build_value(v, item)

        return entry

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

        query = {oattr: names}
        if otype != "*":
            if of.isBaseType(otype):
                query["_type"] = otype
            else:
                query["extension"] = otype
        res = index.search(query, attrs)

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
                    item[attr] = entry[attr] if attr in ['dn', '_type'] else entry[attr][0]
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

    @Command(needsUser=True, __help__=N_("Checks an object of the given type can be placed in the dn"))
    def isContainerForObjectType(self, user, container_dn, object_type):
        container_type_query = self.__session.query(getattr(ObjectInfoIndex, "_type")).filter(
            getattr(ObjectInfoIndex, "dn") == container_dn).one()
        container_type = container_type_query[0]
        allowed = ObjectFactory.getInstance().getAllowedSubElementsForObject(container_type)
        return object_type in allowed

    @Command(needsUser=True, __help__=N_("Returns a list of all containers"))
    def getContainerTree(self, user, base, object_type=None):
        types = []
        table = inspect(ObjectInfoIndex)
        o2 = aliased(ObjectInfoIndex)
        for container in self.containers:
            types.append(getattr(ObjectInfoIndex, "_type") == container)

        query = and_(getattr(ObjectInfoIndex, "_parent_dn") == base, or_(*types))

        query_result = self.__session.query(ObjectInfoIndex, func.count(getattr(o2, "_parent_dn"))) \
            .outerjoin(o2, and_(getattr(o2, "_invisible").is_(False), getattr(o2, "_parent_dn") == getattr(ObjectInfoIndex, "dn"))) \
            .filter(query) \
            .group_by(*table.c)

        res = {}
        factory = ObjectFactory.getInstance()
        for item, children in query_result:
            self.update_res(res, item, user, 1)

            if object_type is not None and item.dn in res:
                res[item.dn]['hasChildren'] = children > 0
                # check if object_type is allowed in this container
                res[item.dn]['allowed_move_target'] = object_type in factory.getAllowedSubElementsForObject(res[item.dn]['tag'],
                                                                                                            includeInvisible=False)
        return res

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
        if 'adjusted-dn' in fltr and fltr['adjusted-dn'] is True:
            dn_hook = "_adjusted_parent_dn"
        actions = 'actions' in fltr and fltr['actions'] is True

        # Sanity checks
        scope = scope.upper()
        if not scope in ["SUB", "BASE", "ONE", "CHILDREN"]:
            raise GOsaException(C.make_error("INVALID_SEARCH_SCOPE", scope=scope))
        if not fltr['mod-time'] in ["hour", "day", "week", "month", "year", "all"]:
            raise GOsaException(C.make_error("INVALID_SEARCH_DATE", date=fltr['mod-time']))

        # Build query: join attributes and keywords
        queries = []

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

        order_by = None
        if 'order-by' in fltr:
            is_desc = 'order' in fltr and fltr['order'] == 'desc'
            order_by = "_last_changed"
            if fltr['order-by'] == "last-changed":
                order_by = "_last_modified"
            order_by = desc(getattr(ObjectInfoIndex, order_by)) if is_desc else getattr(ObjectInfoIndex, order_by)

        # Perform primary query and get collect the results
        squery = []
        these = dict([(x, 1) for x in self.__search_aid['used_attrs']])
        these.update(dict(dn=1, _type=1, _uuid=1, _last_changed=1))
        these = list(these.keys())

        query_result = self.finalize_query(query, fltr, qstring=qstring, order_by=order_by)

        try:
            self.log.debug(str(query_result.statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})))
        except Exception as e:
            self.log.warning(str(e))
            self.log.debug(str(query_result))
            pass

        # limit only secondary enabled searches, because e.g. the treeitems use this search to resolve and we do not want to limit those results
        if fltr['secondary'] == "enabled":
            max_results = self.env.config.get("backend.max-results", default=1000)
        else:
            max_results = math.inf

        counter = 0
        total = query_result.count()
        response = {}
        if total == 0 and fallback is True and PluginRegistry.getInstance("ObjectIndex").fuzzy is True:
            # do fuzzy search
            if qstring:
                try:
                    keywords = [s.strip("'").strip('"') for s in shlex.split(qstring)]
                except ValueError:
                    keywords = [s.strip("'").strip('"') for s in qstring.split(" ")]
                # Make keywords unique
                keywords = list(set(keywords))

                # find most similar words
                for i, kw in enumerate(keywords):
                    r = self.__session.execute("SELECT word FROM unique_lexeme WHERE similarity(word, '{0}') > {1} ORDER BY word <-> '{0}' LIMIT 1;".format(kw, self.__fuzzy_similarity_threshold)).fetchone()
                    keywords[i] = r['word']

                self.log.info("no results found for: '%s' => re-trying with: '%s'" % (qstring, " ".join(keywords)))
                response['orig'] = qstring
                response['fuzzy'] = " ".join(keywords)
                query_result = self.finalize_query(query, fltr, qstring=" ".join(keywords), order_by=order_by)
                total = query_result.count()

        response['primary_total'] = total
        self.log.debug("Query: %s Keywords: %s, Filter: %s => %s results" % (qstring, keywords, fltr, total))

        squery_constraints = {}
        for tuple in query_result:
            item = tuple[0]
            rank = tuple[1]
            self.update_res(res, item, user, rank, these=these, actions=actions)
            counter += 1
            if counter >= max_results:
                break

            # Collect information for secondary search?
            if fltr['secondary'] != "enabled":
                continue

            if item._type in self.__search_aid['resolve']:
                if len(self.__search_aid['resolve'][item._type]) == 0:
                    continue

                kv = self.__index_props_to_key_value(item.properties)
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
                            if tag not in squery_constraints:
                                squery_constraints[tag] = {}
                            if r['filter'] not in squery_constraints[tag]:
                                squery_constraints[tag][r['filter']] = []
                            squery_constraints[tag][r['filter']].append(kv[r['attribute']][0])

        for type, constraints in squery_constraints.items():
            for key, values in constraints.items():
                values = list(set(values))
                if len(values) > 0:
                    squery.append(and_(ObjectInfoIndex._type == type, KeyValueIndex.key == key, KeyValueIndex.value.in_(values)))

        # Perform secondary query and update the result
        if fltr['secondary'] == "enabled" and squery:
            query = or_(*squery)

            # Add "_last_changed" information to query
            if fltr['mod-time'] != "all":
                query = and_(query, ObjectInfoIndex._last_modified >= td)

            # Execute query and update results
            sec_result = self.__session.query(ObjectInfoIndex).join(ObjectInfoIndex.properties).options(contains_eager(ObjectInfoIndex.properties)).filter(query)
            try:
                self.log.debug("Secondary query: %s " % str(sec_result.statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})))
            except Exception as e:
                self.log.warning(str(e))
                self.log.debug("Secondary query: %s " % str(sec_result))
                pass

            total += sec_result.count()
            if counter < max_results:
                for item in sec_result:
                    self.update_res(res, item, user, self.__make_relevance(item, keywords, fltr, True), secondary=True, these=these, actions=actions)
                    counter += 1
                    if counter >= max_results:
                        break

        response['total'] = total
        response['results'] = list(res.values())
        return response

    def finalize_query(self, query, fltr, qstring=None, order_by=None):
        search_query = None
        if qstring is not None:
            search_query = parse_search_query(qstring)
            ft_query = and_(SearchObjectIndex.search_vector.match(search_query, sort=order_by is None, postgresql_regconfig='simple'),
                            SearchObjectIndex.so_uuid == ObjectInfoIndex.uuid,
                            query)
        else:
            ft_query = query

        if search_query is not None:
            query_result = self.__session.query(ObjectInfoIndex, func.ts_rank_cd(
                SearchObjectIndex.search_vector,
                func.to_tsquery(search_query)
            ).label('rank')).options(joinedload(ObjectInfoIndex.search_object)).options(joinedload(ObjectInfoIndex.properties)).filter(ft_query)
        else:
            query_result = self.__session.query(ObjectInfoIndex, "0").options(joinedload(ObjectInfoIndex.properties)).filter(ft_query)

        if order_by is not None:
            query_result = query_result.order_by(order_by)
        elif search_query is not None:
            query_result = query_result.order_by(
                desc(
                    func.ts_rank_cd(
                        SearchObjectIndex.search_vector,
                        func.to_tsquery(search_query)
                    )
                )
            )
        if 'limit' in fltr:
            query_result = query_result.limit(fltr['limit'])
        return query_result

    @Command(needsUser=True, __help__=N_("Filter for indexed attributes and return the matches."))
    def search1(self, user, base, scope, qstring, fltr=None):
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
                            subject.ilike("%" + kw.replace(r"%", "\%") + "%")
                        ))
                    else:
                        res.append(subject.ilike("%" + kw.replace(r"%", "\%") + "%"))
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

            # Only filter for category if desired
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

        order_by = None
        if 'order-by' in fltr:
            is_desc = 'order' in fltr and fltr['order'] == 'desc'
            order_by = "_last_changed"
            if fltr['order-by'] == "last-changed":
                order_by = "_last_modified"
            order_by = desc(getattr(ObjectInfoIndex, order_by)) if is_desc else getattr(ObjectInfoIndex, order_by)

        # Perform primary query and get collect the results
        squery = []
        these = dict([(x, 1) for x in self.__search_aid['used_attrs']])
        these.update(dict(dn=1, _type=1, _uuid=1, _last_changed=1))
        these = list(these.keys())

        query_result = self.__session.query(ObjectInfoIndex).options(joinedload(ObjectInfoIndex.properties)).filter(query)
        if order_by is not None:
            query_result.order_by(order_by)
        if 'limit' in fltr:
            query_result.limit(fltr['limit'])

        try:
            self.log.debug(str(query_result.statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})))
        except Exception:
            pass

        max_results = self.env.config.get("backend.max-results", default=1000)
        counter = 0
        total = query_result.count()
        print("Keywords: %s, Filter: %s" % (keywords, fltr))

        for item in query_result:
            self.update_res(res, item, user, self.__make_relevance(item, keywords, fltr), these=these, actions=actions)
            counter += 1
            if counter >= max_results:
                break

            # Collect information for secondary search?
            if fltr['secondary'] != "enabled":
                continue

            if item._type in self.__search_aid['resolve']:
                if len(self.__search_aid['resolve'][item._type]) == 0:
                    continue

                kv = self.__index_props_to_key_value(item.properties)
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
            sec_result = self.__session.query(ObjectInfoIndex).filter(query)
            total += sec_result.count()
            if counter < max_results:
                for item in sec_result:
                    self.update_res(res, item, user, self.__make_relevance(item, keywords, fltr, True), secondary=True, these=these, actions=actions)
                    counter += 1
                    if counter >= max_results:
                        break

        return {
            "total": total,
            "results": list(res.values())
        }

    def __make_relevance(self, item, keywords, fltr, fuzzy=False):
        """
        Very simple relevance weight-o-meter for search results. To
        be improved...

        It basically takes the item and checks if one of the keyword
        is contained. Takes account on fuzzyness, secondary searches,
        tags.
        """
        penalty = 1

        # Walk thru keywords
        if keywords:

            # Prepare attribute set
            values = []
            for prop in item.properties:
                values.append(prop.value)

            for keyword in keywords:

                # No exact match
                if not keyword in values:
                    penalty /= 2

                # Penalty for not having an case insensitive match
                elif not keyword.lower() in [s.value.lower() for s in item.properties]:
                    penalty /= 4

                # Penalty for not having the correct category
                elif fltr['category'] != "all" and fltr['category'].lower() != item['_type'].lower():
                    penalty /= 2

            # Penalty for not having category in keywords
            if item._type in self.__search_aid['aliases']:
                if not set([t.lower() for t in self.__search_aid['aliases'][item._type]]).intersection(set([k.lower() for k in keywords])):
                    penalty /= 6

        # Penalty for secondary
        if fltr['secondary'] == "enabled":
            penalty /= 10

        # Penalty for fuzzyness
        if fuzzy:
            penalty /= 10

        return penalty

    def update_res(self, res, search_item, user=None, relevance=0, secondary=False, these=None, actions=False):
    
        # Filter out what the current use is not allowed to see
        item = self.__filter_entry(user, search_item, these)
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
                if len(search_item.search_object) == 1 is not None and hasattr(search_item.search_object[0], k) and getattr(search_item.search_object[0], k) is not None:
                    entry[k] = getattr(search_item.search_object[0], k)
                elif v in item and item[v]:
                    if v == "dn":
                        entry[k] = item[v]
                    else:
                        entry[k] = item[v][0]
                else:
                    entry[k] = self.__build_value(v, item)

            entry['container'] = item['_type'] in self.containers

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
        get_attrs = []

        for attr in attrs:
            if attr is not None and these is not None and attr not in these:
                continue

            if attr is not None and self.__has_access_to(user, entry.dn, entry._type, attr):
                if hasattr(ObjectInfoIndex, attr):
                    ne[attr] = getattr(entry, attr)
                else:
                    get_attrs.append(attr)
                    ne[attr] = None

            else:
                ne[attr] = None

        if len(get_attrs):
            kv = self.__index_props_to_key_value(entry.properties)
            for attr in get_attrs:
                ne[attr] = kv[attr] if attr in kv else None

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
