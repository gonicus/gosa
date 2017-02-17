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
from gosa.common.event import EventMaker
from lxml import etree
from lxml import objectify
import zope.event
import datetime
import hashlib
import time
import itertools

from gosa.backend.routes.sse.main import SseHandler
from zope.interface import implementer
from gosa.common import Environment
from gosa.common.utils import N_
from gosa.common.handler import IInterfaceHandler
from gosa.common.components import Command, Plugin, PluginRegistry
from gosa.common.error import GosaErrorHandler as C
from gosa.backend.objects import ObjectFactory, ObjectProxy, ObjectChanged
from gosa.backend.exceptions import FilterException, IndexException, ProxyException, ObjectException
from gosa.backend.lock import GlobalLock
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Boolean, Sequence, DateTime, ForeignKey, or_, and_, not_, func

Base = declarative_base()

# Register the errors handled  by us
C.register_codes(dict(
    OBJECT_EXISTS=N_("Object with UUID %(uuid)s already exists"),
    OBJECT_NOT_FOUND=N_("Cannot find object %(id)s"),
    INDEXING=N_("Index rebuild in progress - try again later"),
    NOT_SUPPORTED=N_("Requested search operation %(operation)s is not supported"),
))


class Schema(Base):
    __tablename__ = 'schema'

    hash = Column(String(32), primary_key=True)

    def __repr__(self):  # pragma: nocover
       return "<Schema(hash='%s')>" % self.hash


class KeyValueIndex(Base):
    __tablename__ = 'kv-index'

    id = Column(Integer, Sequence('kv_id_seq'), primary_key=True, nullable=False)
    uuid = Column(String(36), ForeignKey('obj-index.uuid'))
    key = Column(String(64))
    value = Column(String)

    def __repr__(self):  # pragma: nocover

        return "<KeyValueIndex(uuid='%s', key='%s', value='%s')>" % (self.uuid, self.key, self.value)


class ExtensionIndex(Base):
    __tablename__ = 'ext-index'

    id = Column(Integer, Sequence('ei_id_seq'), primary_key=True, nullable=False)
    uuid = Column(String(36), ForeignKey('obj-index.uuid'))
    extension = Column(String(64))

    def __repr__(self):  # pragma: nocover
       return "<ExtensionIndex(uuid='%s', extension='%s')>" % (
                            self.uuid, self.extension)


class ObjectInfoIndex(Base):
    __tablename__ = 'obj-index'

    uuid = Column(String(36), primary_key=True)
    dn = Column(String)
    _parent_dn = Column(String)
    _adjusted_parent_dn = Column(String)
    _type = Column(String(64))
    _last_modified = Column(DateTime)
    _invisible = Column(Boolean)
    properties = relationship("KeyValueIndex", order_by=KeyValueIndex.key)
    extensions = relationship("ExtensionIndex", order_by=ExtensionIndex.extension)

    def __repr__(self):  # pragma: nocover
       return "<ObjectInfoIndex(uuid='%s', dn='%s', _parent_dn='%s', _adjusted_parent_dn='%s', _type='%s', _last_modified='%s', _invisible='%s')>" % (
                            self.uuid, self.dn, self._parent_dn, self._adjusted_parent_dn, self._type, self._last_modified, self._invisible)

class IndexScanFinished():  # pragma: nocover
    pass


@implementer(IInterfaceHandler)
class ObjectIndex(Plugin):
    """
    The *ObjectIndex* keeps track of objects and their indexed attributes. It
    is the search engine that allows quick queries on the data set with
    paged results and wildcards.
    """

    fuzzy = False
    db = None
    base = None
    __session = None
    _priority_ = 20
    _target_ = 'core'
    _indexed = False
    _post_process_job = None
    importing = False
    to_be_updated = []
    currently_moving = {}
    __search_aid = {}

    def __init__(self):
        self.env = Environment.getInstance()

        # Remove old lock if exists
        if GlobalLock.exists("scan_index"):
            GlobalLock.release("scan_index")

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

        # Do a feature check
        try:
            self.__session.query(KeyValueIndex).filter(func.levenshtein("foo", "foo") < 2).one_or_none()
            self.fuzzy = True
        except:
            self.__session.rollback()

        # If there is already a collection, check if there is a newer schema available
        schema = self.factory.getXMLObjectSchema(True)
        if self.isSchemaUpdated(schema):
            self.__session.query(Schema).delete()
            self.__session.query(KeyValueIndex).delete()
            self.__session.query(ExtensionIndex).delete()
            self.__session.query(ObjectInfoIndex).delete()
            self.log.info('object definitions changed, dropped old object index')

        # Create the initial schema information if required
        if not self.__session.query(Schema).one_or_none():
            self.log.info('created schema')
            md5s = hashlib.md5()
            md5s.update(schema)
            md5sum = md5s.hexdigest()

            schema = Schema(hash=md5sum)
            self.__session.add(schema)
            self.__session.commit()

        # Schedule index sync
        if self.env.config.get("backend.index", "True").lower() == "true":
            import sys
            if hasattr(sys, '_called_from_test'):
                self.sync_index()
            else:
                sobj = PluginRegistry.getInstance("SchedulerService")
                sobj.getScheduler().add_date_job(self.sync_index,
                       datetime.datetime.now() + datetime.timedelta(seconds=1),
                       tag='_internal', jobstore='ram')

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

        # Memorize search information for later use
        self.__search_aid = dict(attrs=attrs,
                                 used_attrs=used_attrs,
                                 mapping=mapping,
                                 resolve=resolve,
                                 aliases=aliases)

    def stop(self):
        if self.__handle_events in zope.event.subscribers:
            zope.event.subscribers.remove(self.__handle_events)

    def is_currently_moving(self, dn, move_target=False):
        if move_target:
            # check for value (the new dn after movement)
            return dn in self.currently_moving.values()
        else:
            # check for key (the old dn before the movement)
            return dn in self.currently_moving.keys()

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
        obj = None

        if not _uuid and not dn:
            return

        # Set importing flag to true in order to be able to post process incoming
        # objects.
        ObjectIndex.importing = True

        # Setup or refresh timer job to run the post processing
        sched = PluginRegistry.getInstance("SchedulerService").getScheduler()
        next_run = datetime.datetime.now() + datetime.timedelta(0, 5)
        if self._post_process_job:
            sched.reschedule_date_job(self._post_process_job, next_run)
        else:
            self._post_process_job = sched.add_date_job(self._post_process_by_timer, next_run, tag='_internal', jobstore="ram", )

        # Resolve dn from uuid if needed
        if not dn:
            dn = self.__session.query(ObjectInfoIndex.dn).filter(ObjectInfoIndex.uuid == _uuid).one_or_none()

        # Modification
        if change_type == "modify":

            # Get object
            obj = self._get_object(dn)
            if not obj:
                return

            # Check if the entry exists - if not, maybe let create it
            entry = self.__session.query(ObjectInfoIndex.dn).filter(
                or_(
                    ObjectInfoIndex.uuid == _uuid,
                    func.lower(ObjectInfoIndex.dn) == func.lower(dn)
                )).one_or_none()
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
            if _uuid is not None:
                self.remove_by_uuid(_uuid)
            else:
                obj = self._get_object(dn)
                if not obj:
                    return

                self.remove(obj)

        # Move
        if change_type in ['modrdn', 'moddn']:

            # Get object
            obj = self._get_object(new_dn)
            if not obj:
                return

            # Check if the entry exists - if not, maybe let create it
            entry = self.__session.query(ObjectInfoIndex.dn).filter(
                or_(
                    ObjectInfoIndex.uuid == _uuid,
                    func.lower(ObjectInfoIndex.dn) == func.lower(dn)
                )).one_or_none()

            if entry:
                self.update(obj)

            else:
                self.insert(obj)

        # send the event to the clients
        event_change_type = "update"
        if change_type == "add":
            event_change_type = "create"
        elif change_type == "delete":
            event_change_type = "remove"

        e = EventMaker()
        if obj:
            ev = e.Event(e.ObjectChanged(
                e.UUID(obj.uuid),
                e.DN(obj.dn),
                e.ModificationTime(_last_changed.strftime("%Y%m%d%H%M%SZ")),
                e.ChangeType(event_change_type)
            ))
        else:
            ev = e.Event(e.ObjectChanged(
                e.UUID(_uuid),
                e.DN(dn),
                e.ModificationTime(_last_changed.strftime("%Y%m%d%H%M%SZ")),
                e.ChangeType(event_change_type)
            ))

        event = "<?xml version='1.0'?>\n%s" % etree.tostring(ev, pretty_print=True).decode('utf-8')

        # Validate event
        xml = objectify.fromstring(event, PluginRegistry.getEventParser())

        SseHandler.notify(xml, channel="broadcast")

    def _post_process_by_timer(self):
        self._post_process_job = None
        self.post_process()

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

        stored_md5sum = self.__session.query(Schema.hash).one_or_none()
        if stored_md5sum and stored_md5sum[0] == md5sum:
            return False

        return True

    def sync_index(self):
        # Don't index if someone else is already doing it
        if GlobalLock.exists("scan_index"):
            return

        # Don't run index, if someone else already did until the last
        # restart.
        cr = PluginRegistry.getInstance("CommandRegistry")
        GlobalLock.acquire("scan_index")
        ObjectIndex.importing = True

        try:
            self._indexed = True

            t0 = time.time()

            def resolve_children(dn):
                self.log.debug("found object '%s'" % dn)
                res = {}

                children = self.factory.getObjectChildren(dn)
                res = {**res, **children}

                for chld in children.keys():
                    res = {**res, **resolve_children(chld)}

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
                last_modified = self.__session.query(ObjectInfoIndex._last_modified).filter(ObjectInfoIndex.uuid == obj.uuid).one_or_none()

                # Entry is not in the database
                if not last_modified:
                    self.insert(obj, True)

                # Entry is in the database
                else:
                    # OK: already there
                    if obj.modifyTimestamp == last_modified[0]:
                        self.log.debug("found up-to-date object index for %s" % obj.uuid)

                    else:
                        self.log.debug("updating object index for %s" % obj.uuid)
                        self.update(obj)

                backend_objects.append(obj.uuid)
                del obj

            # Remove entries that are in the index, but not in any other backends
            for uuid in self.__session.query(ObjectInfoIndex.uuid).all():
                uuid = uuid[0]
                if uuid not in backend_objects:
                    self.remove_by_uuid(uuid)

            t1 = time.time()
            self.log.info("processed %d objects in %ds" % (len(res), t1 - t0))

        except Exception as e:
            self.log.critical("building the index failed: %s" % str(e))
            import traceback
            traceback.print_exc()

        finally:
            self.post_process()
            self.log.info("index refresh finished")

            zope.event.notify(IndexScanFinished())
            GlobalLock.release("scan_index")

    def post_process(self):
        ObjectIndex.importing = False

        # Some object may have queued themselves to be re-indexed, process them now.
        self.log.info("need to refresh index for %d objects" % (len(ObjectIndex.to_be_updated)))
        for uuid in ObjectIndex.to_be_updated:
            dn = self.__session.query(ObjectInfoIndex.dn).filter(ObjectInfoIndex.uuid == uuid).one_or_none()

            if dn:
                obj = ObjectProxy(dn[0])
                self.update(obj)

        ObjectIndex.to_be_updated = []

    def index_active(self):  # pragma: nocover
        return self._indexed

    def __handle_events(self, event):
        if isinstance(event, objectify.ObjectifiedElement):
            self.__backend_change_processor(event)

        elif isinstance(event, ObjectChanged):
            change_type = None
            _uuid = event.uuid
            _dn = None
            _last_changed = datetime.datetime.now()

            # Try to find the affected DN
            e = self.__session.query(ObjectInfoIndex).filter(ObjectInfoIndex.uuid == _uuid).one_or_none()
            if e:

                # New pre-events don't have a dn. Just skip is in this case...
                if hasattr(e, 'dn'):
                    _dn = e.dn
                    _last_changed = e._last_modified
                else:
                    _dn = "not known yet"

            if event.reason == "post object remove":
                self.log.debug("removing object index for %s" % _uuid)
                self.remove_by_uuid(_uuid)
                change_type = "remove"

            if event.reason == "pre object move":
                self.log.debug("starting object movement from %s to %s" % (_dn, event.dn))
                self.currently_moving[_dn] = event.dn

            if event.reason == "post object move":
                self.log.debug("updating object index for %s" % _uuid)
                obj = ObjectProxy(event.dn)
                self.update(obj)
                _dn = obj.dn
                change_type = "move"
                if event.orig_dn in self.currently_moving:
                    del self.currently_moving[event.orig_dn]

            if event.reason == "post object create":
                self.log.debug("creating object index for %s" % _uuid)
                obj = ObjectProxy(event.dn)
                self.insert(obj)
                _dn = obj.dn
                change_type = "create"

            if event.reason in ["post object update"]:
                self.log.debug("updating object index for %s" % _uuid)
                if not event.dn:
                    dn = self.__session.query(ObjectInfoIndex.dn).filter(ObjectInfoIndex.uuid == _uuid).one_or_none()
                    if dn:
                        event.dn = dn

                obj = ObjectProxy(event.dn)
                self.update(obj)
                change_type = "update"

            # send the event to the clients
            e = EventMaker()

            if event.reason[0:4] == "post" and _uuid and _dn and change_type:

                ev = e.Event(e.ObjectChanged(
                    e.UUID(_uuid),
                    e.DN(_dn),
                    e.ModificationTime(_last_changed.strftime("%Y%m%d%H%M%SZ")),
                    e.ChangeType(change_type)
                ))
                event = "<?xml version='1.0'?>\n%s" % etree.tostring(ev, pretty_print=True).decode('utf-8')

                # Validate event
                xml = objectify.fromstring(event, PluginRegistry.getEventParser())

                SseHandler.notify(xml, channel="broadcast")

    def insert(self, obj, skip_base_check=False):
        if not skip_base_check:
            pdn = self.__session.query(ObjectInfoIndex.dn).filter(ObjectInfoIndex.dn == obj.get_parent_dn()).one_or_none()

            # No parent?
            if not pdn:
                self.log.debug("ignoring object that has no base in the current index: " + obj.dn)
                return

            parent = self._get_object(obj.get_parent_dn())
            if not parent.can_host(obj.get_base_type()):
                self.log.debug("ignoring object that is not relevant for the index: " + obj.dn)
                return

        self.log.debug("creating object index for %s" % obj.uuid)

        uuid = self.__session.query(ObjectInfoIndex.uuid).filter(ObjectInfoIndex.uuid == obj.uuid).one_or_none()
        if uuid:
            raise IndexException(C.make_error('OBJECT_EXISTS', "base", uuid=obj.uuid))

        self.__save(obj.asJSON(True))

    def __save(self, data):

        # Assemble object index object
        oi = ObjectInfoIndex(
            uuid=data["_uuid"],
            dn=data["dn"],
            _type=data["_type"],
            _parent_dn=data["_parent_dn"],
            _adjusted_parent_dn=data["_adjusted_parent_dn"],
            _invisible=data["_invisible"]
        )

        if '_last_changed' in data:
            oi._last_modified = datetime.datetime.fromtimestamp(data["_last_changed"])

        self.__session.add(oi)

        # Assemble extension index objects
        for ext in data["_extensions"]:
            ei = ExtensionIndex(uuid=data["_uuid"], extension=ext)
            self.__session.add(ei)

        # Assemble key value index objects
        for key, value in data.items():

            # Skip meta information and DN
            if key.startswith("_") or key == "dn":
                continue

            if isinstance(value, list):
                for v in value:
                    kvi = KeyValueIndex(uuid=data["_uuid"], key=key, value=v)
                    self.__session.add(kvi)
            else:
                kvi = KeyValueIndex(uuid=data["_uuid"], key=key, value=value)
                self.__session.add(kvi)

        self.__session.commit()

    def remove(self, obj):
        self.remove_by_uuid(obj.uuid)

    def remove_by_uuid(self, uuid):
        self.log.debug("removing object index for %s" % uuid)

        if self.exists(uuid):
            self.__session.query(KeyValueIndex).filter(KeyValueIndex.uuid == uuid).delete()
            self.__session.query(ExtensionIndex).filter(ExtensionIndex.uuid == uuid).delete()
            self.__session.query(ObjectInfoIndex).filter(ObjectInfoIndex.uuid == uuid).delete()
            self.__session.commit()

    def update(self, obj):
        # Gather information
        current = obj.asJSON(True)
        old_dn = self.__session.query(ObjectInfoIndex.dn).filter(ObjectInfoIndex.uuid == obj.uuid).one_or_none()
        if not old_dn:
            raise IndexException(C.make_error('OBJECT_NOT_FOUND', "base", id=obj.uuid))
        old_dn = old_dn[0]

        # Remove old entry and insert new
        self.remove_by_uuid(obj.uuid)
        self.__save(current)

        # Has the entry been moved?
        if current['dn'] != old_dn:

            # Adjust all ParentDN entries of child objects
            res = self.__session.query(ObjectInfoIndex).filter(
                or_(ObjectInfoIndex._parent_dn == old_dn, ObjectInfoIndex._parent_dn.like('%' + old_dn))
            ).all()

            for entry in res:
                o_uuid = entry.uuid
                o_dn = entry.dn
                o_parent = entry._parent_dn
                o_adjusted_parent = entry._adjusted_parent_dn

                n_dn = o_dn[:-len(old_dn)] + current['dn']
                n_parent = o_parent[:-len(old_dn)] + current['dn']
                n_adjusted_parent = o_adjusted_parent[:-len(o_adjusted_parent)] + current['_adjusted_parent_dn']

                oi = self.__session.query(ObjectInfoIndex).filter(ObjectInfoIndex.uuid == o_uuid).one()
                oi.dn = n_dn
                oi._parent_dn = n_parent
                oi._adjusted_parent_dn = n_adjusted_parent

                self.__session.commit()

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
        return self.__session.query(ObjectInfoIndex.uuid).filter(ObjectInfoIndex.uuid == uuid).one_or_none() is not None

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
        Perform a raw sqlalchemy query.

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
            conditions['type'] = 1

        else:
            conditions = None

        if not isinstance(query, dict):
            raise FilterException(C.make_error('INVALID_QUERY'))

        # Create result-set
        for item in self.search(query, conditions):
            # Filter out what the current use is not allowed to see
            item = self.__filter_entry(user, item)
            if item and item['dn'] is not None:
                res.append(item)

        return res

    def _make_filter(self, node):
        use_key_value = False
        use_extension = False

        def __make_filter(n):
            nonlocal use_key_value
            nonlocal use_extension

            res = []

            for key, value in n.items():
                if isinstance(value, dict):

                    # Maintain certain key words
                    if key == "and_":
                        res.append(and_(*__make_filter(value)))
                    elif key == "or_":
                        res.append(or_(*__make_filter(value)))
                    elif key == "not_":
                        res.append(not_(*__make_filter(value)))
                    else:
                        raise IndexException(C.make_error('NOT_SUPPORTED', "base", operator=key))

                elif isinstance(value, list):
                    # implicit or_ in case of lists - hashes cannot have multiple
                    # keys with the same name
                    exprs = []
                    for v in value:
                        if hasattr(ObjectInfoIndex, key):
                            if "%" in v:
                                exprs.append(getattr(ObjectInfoIndex, key).like(v))
                            else:
                                exprs.append(getattr(ObjectInfoIndex, key) == v)
                        elif key == "extension":
                            use_extension = True
                            exprs.append(ExtensionIndex.extension == v)
                        else:
                            use_key_value = True
                            if "%" in v:
                                exprs.append(and_(KeyValueIndex.key == key, KeyValueIndex.value.like(v)))
                            else:
                                exprs.append(and_(KeyValueIndex.key == key, KeyValueIndex.value == v))

                    res.append(or_(*exprs))

                else:
                    if hasattr(ObjectInfoIndex, key):
                        if "%" in value:
                            res.append(getattr(ObjectInfoIndex, key).like(value))
                        else:
                            res.append(getattr(ObjectInfoIndex, key) == value)
                    elif key == "extension":
                        use_extension = True
                        res.append(ExtensionIndex.extension == value)
                    else:
                        use_key_value = True
                        if "%" in value:
                            res.append(and_(KeyValueIndex.key == key, KeyValueIndex.value.like(value)))
                        else:
                            res.append(and_(KeyValueIndex.key == key, KeyValueIndex.value == value))

            return res

        # Add query information to be able to search various tables
        _args = __make_filter(node)

        if use_extension and use_key_value:
            args = [ObjectInfoIndex.uuid == KeyValueIndex.uuid, ObjectInfoIndex.uuid == ExtensionIndex.uuid]
            args += _args
            return and_(*args)

        if use_extension:
            args = [ObjectInfoIndex.uuid == ExtensionIndex.uuid]
            args += _args
            return and_(*args)

        if use_key_value:
            args = [ObjectInfoIndex.uuid == KeyValueIndex.uuid]
            args += _args
            return and_(*args)

        return _args

    def search(self, query, properties):
        """
        Perform an index search

        ========== ==================
        Parameter  Description
        ========== ==================
        query      Query hash
        properties Conditions hash
        ========== ==================

        For more information on the query format, consult the mongodb documentation.

        ``Return``: List of dicts
        """
        res = []
        fltr = self._make_filter(query)

        def normalize(data, resultset=None):
            _res = {
                "_uuid": data.uuid,
                "dn": data.dn,
                "_type": data._type,
                "_parent_dn": data._parent_dn,
                "_adjusted_parent_dn": data._adjusted_parent_dn,
                "_last_changed": data._last_modified,
                "_extensions": []
            }

            # Add extension list
            for extension in data.extensions:
                _res["_extensions"].append(extension.extension)

            # Add indexed properties
            for kv in data.properties:
                if kv.key in _res:
                    _res[kv.key].append(kv.value)

                else:
                    _res[kv.key] = [kv.value]

            # Clean the result set?
            if resultset:
                for key in [_key for _key in _res if not _key in resultset.keys() and _key[0:1] != "_"]:
                    _res.pop(key, None)

            return _res

        q = self.__session.query(ObjectInfoIndex).filter(*fltr)
        for o in q.all():
            res.append(normalize(o, properties))

        return res

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
