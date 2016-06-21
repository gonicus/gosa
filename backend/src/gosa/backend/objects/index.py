# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
Object Index
============

The Object Index is the search engine in GOsa. It keeps track about
all defined object types and can find references to it inside of its
local index database

----
"""
import logging
import zope.event
import datetime
import re
import hashlib
import time
import itertools
from zope.interface import implementer
from gosa.common.components.jsonrpc_utils import Binary as CBinary
from gosa.common import Environment
from gosa.common.utils import N_
from gosa.common.handler import IInterfaceHandler
from gosa.common.components import Command, Plugin, PluginRegistry
from gosa.common.error import GosaErrorHandler as C
from gosa.backend.objects import ObjectFactory, ObjectProxy, ObjectChanged
from gosa.backend.exceptions import ProxyException, ObjectException, FilterException, IndexException
from gosa.backend.lock import GlobalLock
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime

Base = declarative_base()

# Register the errors handled  by us
C.register_codes(dict(
    OBJECT_EXISTS=N_("Object with UUID %(uuid)s already exists"),
    OBJECT_NOT_FOUND=N_("Cannot find object %(id)s"),
    INDEXING=N_("index rebuild in progress - try again later")
))


class Schema(Base):
    __tablename__ = 'schema'

    hash = Column(String(32), primary_key=True)

    def __repr__(self):
       return "<Schema(hash='%s')>" % self.hash


class KeyValueIndex(Base):
    __tablename__ = 'kv-index'

    uuid = Column(String(36), primary_key=True)
    key = Column(String(64))
    value = Column(String)

    def __repr__(self):
       return "<KeyValueIndex(uuid='%s', key='%s', value='%s')>" % (
                            self.uuid, self.key, self.value)


class ExtensionIndex(Base):
    __tablename__ = 'ext-index'

    uuid = Column(String(36), primary_key=True)
    extension = Column(String(64))

    def __repr__(self):
       return "<ExtensionIndex(uuid='%s', extension='%s')>" % (
                            self.uuid, self.extension)


class ObjectIndex(Base):
    __tablename__ = 'obj-index'

    uuid = Column(String(36), primary_key=True)
    dn = Column(String)
    parent_dn = Column(String)
    adjusted_parent_dn = Column(String)
    type = Column(String(64))
    last_modified = Column(DateTime)

    def __repr__(self):
       return "<ObjectIndex(uuid='%s', dn='%s', parent_dn='%s', adjusted_parent_dn'%s', type='%s', last_modified='%s')>" % (
                            self.uuid, self.dn, self.parent_dn, self.adjusted_parent_dn, self.type, self.last_modified)


class IndexScanFinished():
    pass

@implementer(IInterfaceHandler)
class ObjectIndex(Plugin):
    """
    The *ObjectIndex* keeps track of objects and their indexed attributes. It
    is the search engine that allows quick querries on the data set with
    paged results and wildcards.
    """

    db = None
    base = None
    __session = None
    _priority_ = 20
    _target_ = 'core'
    _indexed = False
    first_run = False
    to_be_updated = []

    def __init__(self):
        self.env = Environment.getInstance()

        self.log = logging.getLogger(__name__)
        self.log.info("initializing object index handler")
        self.factory = ObjectFactory.getInstance()

        # Listen for object events
        zope.event.subscribers.append(self.__handle_events)

    def serve(self):
        # Configure database for the index
        Base.metadata.create_all(self.env.getDatabaseEngine("backend-database"))

        # Store DB session
        self.__session = self.env.getDatabaseSession("backend-database")

        # If there is already a collection, check if there is a newer schema available
        schema = self.factory.getXMLObjectSchema(True)
        if self.isSchemaUpdated(schema):
            self.__session.query(Schema).delete()
            self.__session.query(KeyValueIndex).delete()
            self.__session.query(ExtensionIndex).delete()
            self.__session.query(ObjectIndex).delete()
            self.log.info('object definitions changed, dropped old object index collection')

        # HIER---------------

        # Create the initial schema information if required
        if not "index" in self.db.collection_names():
            self.log.info('created object index collection')
            md5s = hashlib.md5()
            md5s.update(schema)
            md5sum = md5s.hexdigest()

            self.db.index.save({'schema': {'checksum': md5sum}})

        # Sync index
        if self.env.config.get("agent.index", "True").lower() == "true":
            sobj = PluginRegistry.getInstance("SchedulerService")
            sobj.getScheduler().add_date_job(self.sync_index,
                    datetime.datetime.now() + datetime.timedelta(seconds=30),
                    tag='_internal', jobstore='ram')

        # Ensure basic index for the objects
        for index in ['dn', '_uuid', '_last_changed', '_type', '_extensions', '_container', '_parent_dn']:
            self.db.index.ensure_index(index)

        # Extract search aid
        attrs = {}
        mapping = {}
        resolve = {}
        aliases = {}

        for otype in self.factory.getObjectTypes():

            # Assemble search aid
            item = self.factory.getObjectSearchAid(otype)

            if not item:
                continue

            typ = item['type']
            aliases[typ] = [typ]

            if not typ in attrs:
                attrs[typ] = []
            if not typ in resolve:
                resolve[typ] = []
            if not typ in mapping:
                mapping[typ] = dict(dn="dn", title="title", description="description", icon=None)

            attrs[typ] += item['search']

            if 'keyword' in item:
                aliases[typ] += item['keyword']
            if 'map' in item:
                mapping[typ].update(item['map'])
            if 'resolve' in item:
                resolve[typ] += item['resolve']

        # Add index for attribute used for filtering and memorize
        # attributes potentially needed for queries.
        tmp = [x for x in attrs.values()]
        used_attrs = list(itertools.chain.from_iterable(tmp))
        used_attrs += list(itertools.chain.from_iterable([x.values() for x in mapping.values()]))
        used_attrs += list(set(itertools.chain.from_iterable([[x[0]['filter'], x[0]['attribute']] for x in resolve.values() if len(x)])))
        used_attrs = list(set(used_attrs))

        # Remove potentially not assigned values
        used_attrs = [u for u in used_attrs if u]

        # Prepare index
        indices = [x['key'][0][0] for x in self.db.index.index_information().values()]
        binaries = self.factory.getBinaryAttributes()

        # Remove index that is not in use anymore
        for attr in indices:
            if not attr in used_attrs and not attr in ['dn', '_id', '_uuid', '_last_changed', '_type', '_extensions', '_container', '_parent_dn']:
                self.log.debug("removing obsolete index for '%s'" % attr)
                try:
                    self.db.index.drop_index(attr)
                except pymongo.errors.OperationFailure:
                    pass

        # Ensure index for all attributes that want an index
        for attr in used_attrs[:39]:

            # Skip non attribute values
            if '%' in attr or attr in binaries:
                self.log.debug("not adding index for '%s'" % attr)
                continue

            # Add index if it doesn't exist already
            if not attr in indices:
                self.log.debug("adding index for '%s'" % attr)
                self.db.index.ensure_index(attr)

        # Memorize search information for later use
        self.__search_aid = dict(attrs=attrs,
                                 used_attrs=used_attrs,
                                 mapping=mapping,
                                 resolve=resolve,
                                 aliases=aliases)

        #TODO: implement an external event send/subscribe mechanism via SSE/RPC/ROUTING/WHATEVER and
        #      re-enable the ability to update ourself
        # Add event processor
        #amqp = PluginRegistry.getInstance('AMQPHandler')
        #EventConsumer(self.env,
        #    amqp.getConnection(),
        #    xquery="""
        #        declare namespace f='http://www.gonicus.de/Events';
        #        let $e := ./f:Event
        #        return $e/f:BackendChange
        #    """,
        #    callback=self.__backend_change_processor)

    def __backend_change_processor(self, data):
        """
        This method gets called if an external backend reports
        a modification of an entry under its hood.

        We use it to update / create / delete existing index
        entries.
        """
        data = data.BackendChange
        dn = data.DN.text if hasattr(data, 'DN') else None
        new_dn = data.NewDN.text if hasattr(data, 'NewDN') else None
        change_type = data.ChangeType.text
        _uuid = data.UUID.text if hasattr(data, 'UUID') else None
        _last_changed = datetime.datetime.strptime(data.ModificationTime.text, "%Y%m%d%H%M%SZ")

        # Resolve dn from uuid if needed
        if not dn:
            entry = self.db.index.find_one({'_uuid': _uuid}, {'dn': 1})
            if entry:
                dn = entry['dn']

        # Modification
        if change_type == "modify":

            # Get object
            obj = self._get_object(dn)
            if not obj:
                return

            # Check if the entry exists - if not, maybe let create it
            entry = self.db.index.find_one({'$or': [{'dn': re.compile(r'^%s$' %
                re.escape(dn), re.IGNORECASE)}, {'_uuid': _uuid}]}, {'_last_changed': 1})

            if entry:
                self.update(obj)

            else:
                self.insert(obj)

        # Add
        if change_type == "add":

            # Get object
            obj = self._get_object(dn)
            if not obj:
                return

            self.insert(obj)

        # Delete
        if change_type == "delete":
            self.log.info("object has changed in backend: indexing %s" % dn)
            self.log.warning("external delete might not take care about references")
            self.db.index.remove({'dn': dn})

        # Move
        if change_type in ['modrdn', 'moddn']:

            # Get object
            obj = self._get_object(new_dn)
            if not obj:
                return

            # Check if the entry exists - if not, maybe let create it
            entry = self.db.index.find_one({'$or': [{'dn': re.compile(r'^%s$' % re.escape(new_dn), re.IGNORECASE)}, {'_uuid': _uuid}]}, {'_last_changed': 1})

            if entry and obj:
                self.update(obj)

            else:
                self.insert(obj)

    def _get_object(self, dn):
        try:
            obj = ObjectProxy(dn)

        except ProxyException as e:
            self.log.warning("not found %s: %s" % (dn, str(e)))
            obj = None

        except ObjectException as e:
            self.log.warning("not indexing %s: %s" % (dn, str(e)))
            obj = None

        return obj

    def get_search_aid(self):
        return self.__search_aid

    def isSchemaUpdated(self, schema):
        # Calculate md5 checksum for potentially new schema
        md5s = hashlib.md5()
        md5s.update(schema)
        md5sum = md5s.hexdigest()

        return self.__session.query(Schema.hash).one_or_none() != md5sum

    def sync_index(self):
        # Don't index if someone else is already doing it
        if GlobalLock.exists():
            return

        # Don't run index, if someone else already did until the last
        # restart.
        cr = PluginRegistry.getInstance("CommandRegistry")
        nodes = cr.getNodes()
        if len([n for n, v in nodes.items() if 'Indexed' in v and v['Indexed']]):
            return

        GlobalLock.acquire()

        ObjectIndex.first_run = True

        try:
            self._indexed = True

            t0 = time.time()

            def resolve_children(dn):
                self.log.debug("found object '%s'" % dn)
                res = {}

                children = self.factory.getObjectChildren(dn)
                res = dict(res.items() + children.items())

                for chld in children.keys():
                    res = dict(res.items() + resolve_children(chld).items())

                return res

            self.log.info("scanning for objects")
            res = resolve_children(self.env.base)
            res[self.env.base] = 'dummy'

            self.log.info("generating object index")

            # Find new entries
            backend_objects = []
            for o in sorted(res.keys(), key=len):

                # Get object
                try:
                    obj = ObjectProxy(o)

                except ProxyException as e:
                    self.log.warning("not indexing %s: %s" % (o, str(e)))
                    continue

                except ObjectException as e:
                    self.log.warning("not indexing %s: %s" % (o, str(e)))
                    continue

                # Check for index entry
                indexEntry = self.db.index.find_one({'_uuid': obj.uuid}, {'_last_changed': 1})

                # Entry is not in the database
                if not indexEntry:
                    self.insert(obj)

                # Entry is in the database
                else:
                    # OK: already there
                    if obj.modifyTimestamp == indexEntry['_last_changed']:
                        self.log.debug("found up-to-date object index for %s" % obj.uuid)

                    else:
                        self.log.debug("updating object index for %s" % obj.uuid)
                        self.update(obj)

                backend_objects.append(obj.uuid)
                del obj

            # Remove entries that are in the index, but not in any other backends
            for entry in self.db.index.find({'_uuid': {'$exists': True}}, {'_uuid': 1}):
                if entry['_uuid'] not in backend_objects:
                    self.remove_by_uuid(entry['_uuid'])

            t1 = time.time()
            self.log.info("processed %d objects in %ds" % (len(res), t1 - t0))

        except Exception as e:
            self.log.critical("building the index failed: %s" % str(e))
            import traceback
            traceback.print_exc()

        finally:
            ObjectIndex.first_run = False

            # Some object may have queued themselves to be re-indexed, process them now.
            self.log.info("need to refresh index for %d objects" % (len(ObjectIndex.to_be_updated)))
            for uuid in ObjectIndex.to_be_updated:
                entry = self.db.index.find_one({'_uuid': uuid, 'dn': {'$exists': True}}, {'dn': 1})

                if entry:
                    obj = ObjectProxy(entry['dn'])
                    self.update(obj)

            self.log.info("index refresh finished")

            zope.event.notify(IndexScanFinished())
            GlobalLock.release()

    def index_active(self):
        return self._indexed

    def __handle_events(self, event):

        if isinstance(event, ObjectChanged):
            change_type = None
            _uuid = event.uuid
            _dn = None
            _last_changed = time.mktime(datetime.datetime.now().timetuple())

            # Try to find the affected DN
            e = self.db.index.find_one({'_uuid': _uuid}, {'dn': 1, '_last_changed': 1})
            if e:

                # New pre-events don't have a dn. Just skip is in this case...
                if 'dn' in e:
                    _dn = e['dn']
                    _last_changed = e['_last_changed']
                else:
                    _dn = "not known yet"
                    _last_changed = datetime.datetime.now()

            if event.reason == "post object remove":
                self.log.debug("removing object index for %s" % _uuid)
                self.remove_by_uuid(_uuid)
                change_type = "remove"

            if event.reason == "post object move":
                self.log.debug("updating object index for %s" % _uuid)
                obj = ObjectProxy(event.dn)
                self.update(obj)
                _dn = obj.dn
                change_type = "move"

            if event.reason == "post object create":
                self.log.debug("creating object index for %s" % _uuid)
                obj = ObjectProxy(event.dn)
                self.insert(obj)
                _dn = obj.dn
                change_type = "create"

            if event.reason in ["post object update"]:
                self.log.debug("updating object index for %s" % _uuid)
                if not event.dn:
                    entry = self.db.index.find_one({'_uuid': _uuid, 'dn': {'$exists': 1}}, {'dn': 1})
                    if entry:
                        event.dn = entry['dn']

                obj = ObjectProxy(event.dn)
                self.update(obj)
                change_type = "update"

    def insert(self, obj):
        self.log.debug("creating object index for %s" % obj.uuid)

        # If this is the root node, add the root document
        if self.db.index.find_one({'_uuid': obj.uuid}, {'_uuid': 1}):
            raise IndexException(C.make_error('OBJECT_EXISTS', "base", uuid=obj.uuid))

        self.db.index.save(obj.asJSON(True))

    def remove(self, obj):
        self.remove_by_uuid(obj.uuid)

    def remove_by_uuid(self, uuid):
        self.log.debug("removing object index for %s" % uuid)
        if self.exists(uuid):
            self.db.index.remove({'_uuid': uuid})

    def update(self, obj):
        # Gather information
        current = obj.asJSON(True)
        saved = self.db.index.find_one({'_uuid': obj.uuid})
        if not saved:
            raise IndexException(C.make_error('OBJECT_NOT_FOUND', "base", id=obj.uuid))

        # Remove old entry and insert new
        self.remove_by_uuid(obj.uuid)
        self.db.index.save(obj.asJSON(True))

        # Has the entry been moved?
        if current['dn'] != saved['dn']:

            # Adjust all ParentDN entries of child objects
            res = self.db.index.find(
                {'_parent_dn': re.compile('^(.*,)?%s$' % re.escape(saved['dn']))},
                {'_uuid': 1, 'dn': 1, '_parent_dn': 1})

            for entry in res:
                o_uuid = entry['_uuid']
                o_dn = entry['dn']
                o_parent = entry['_parent_dn']

                n_dn = o_dn[:-len(saved['dn'])] + current['dn']
                n_parent = o_parent[:-len(saved['dn'])] + current['dn']

                self.db.index.update({'_uuid': o_uuid}, {
                        '$set': {'dn': n_dn, '_parent_dn': n_parent}})

    @Command(__help__=N_("Check if an object with the given UUID exists."))
    def exists(self, uuid):
        """
        Do a database query for the given UUID and return an
        existance flag.

        ========== ==================
        Parameter  Description
        ========== ==================
        uuid       Object identifier
        ========== ==================

        ``Return``: True/False
        """
        return self.db.index.find_one({'_uuid': uuid}, {'_uuid': 1}) is not None

    @Command(__help__=N_("Get list of defined base object types."))
    def getBaseObjectTypes(self):
        ret = []
        for k, v in self.factory.getObjectTypes().items():
            if v['base']:
                ret.append(k)

        return ret

    @Command(needsUser=True, __help__=N_("Query the index for entries."))
    def find(self, user, query, conditions=None):
        """
        Perform a raw mongodb find call.

        ========== ==================
        Parameter  Description
        ========== ==================
        query      Query hash
        conditions Conditions hash
        ========== ==================

        For more information on the query format, consult the mongodb documentation.

        ``Return``: List of dicts
        """
        res = []

        # Always return dn and _type - we need it for ACL control
        if isinstance(conditions, dict):
            conditions['dn'] = 1
            conditions['_type'] = 1

        else:
            conditions = None

        if not isinstance(query, dict):
            raise FilterException(C.make_error('INVALID_QUERY'))

        # Create result-set
        for item in self.search(query, conditions):

            # Filter out what the current use is not allowed to see
            item = self.__filter_entry(user, item)
            if item and item['dn'] is not None:
                del item['_id']

                # Convert binary (bson) to Binary
                for key in item.keys():
                    if isinstance(item[key], list):

                        n = []
                        for v in item[key]:
                            if isinstance(v, Binary):
                                v = CBinary(v)

                            n.append(v)

                        item[key] = n

                    elif isinstance(item[key], Binary):
                        item[key] = CBinary(item[key])

                res.append(item)

        return res

    def search(self, query, conditions):
        """
        Perform a raw mongodb find call.

        ========== ==================
        Parameter  Description
        ========== ==================
        query      Query hash
        conditions Conditions hash
        ========== ==================

        For more information on the query format, consult the mongodb documentation.

        ``Return``: List of dicts
        """

        if GlobalLock.exists("scan_index"):
            raise FilterException(C.make_error('INDEXING', "base"))

        return self.db.index.find(query, conditions)

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

        res = {}
        for attr in entry.keys():
           if attr in ['dn', '_type', '_uuid', '_last_changed']:
                res[attr] = entry[attr]
                continue

           if self.__has_access_to(user, entry['dn'], entry['_type'], attr):
                res[attr] = entry[attr]

        return res

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
