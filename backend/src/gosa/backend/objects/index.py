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

import re

import ldap
import sqlalchemy
from sqlalchemy.dialects import postgresql
from sqlalchemy_searchable import make_searchable
from sqlalchemy_utils import TSVectorType

import gosa
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
from sqlalchemy.orm import relationship, joinedload
from sqlalchemy import Column, String, Integer, Boolean, Sequence, DateTime, ForeignKey, or_, and_, not_, func, orm

Base = declarative_base()
make_searchable()


# Register the errors handled  by us
C.register_codes(dict(
    OBJECT_EXISTS=N_("Object with UUID %(uuid)s already exists"),
    OBJECT_NOT_FOUND=N_("Cannot find object %(id)s"),
    INDEXING=N_("Index rebuild in progress - try again later"),
    NOT_SUPPORTED=N_("Requested search operator %(operator)s is not supported"),
))


class Schema(Base):
    __tablename__ = 'schema'

    hash = Column(String(32), primary_key=True)

    def __repr__(self):  # pragma: nocover
       return "<Schema(hash='%s')>" % self.hash


class SearchObjectIndex(Base):
    __tablename__ = "so_index"
    so_uuid = Column(String(36), ForeignKey('obj-index.uuid'), primary_key=True)
    reverse_parent_dn = Column(String, index=True)
    title = Column(String)
    description = Column(String)
    search = Column(String)
    types = Column(String)
    search_vector = Column(TSVectorType('title', 'description', 'search', 'types',
                                        weights={'title': 'A', 'types': 'B', 'description': 'C', 'search': 'C'},
                                        regconfig='pg_catalog.simple'
                                        ))
    object = relationship("ObjectInfoIndex", uselist=False, back_populates="search_object")

    def __repr__(self):  # pragma: nocover

        return "<SearchObjectIndex(so_uuid='%s', reverse_dn='%s', title='%s', description='%s')>" % \
               (self.so_uuid, self.reverse_dn, self.title, self.description)


class KeyValueIndex(Base):
    __tablename__ = 'kv-index'

    key_id = Column(Integer, Sequence('kv_id_seq'), primary_key=True, nullable=False)
    uuid = Column(String(36), ForeignKey('obj-index.uuid'))
    key = Column(String(64), index=True)
    value = Column(String)

    def __repr__(self):  # pragma: nocover

        return "<KeyValueIndex(uuid='%s', key='%s', value='%s')>" % (self.uuid, self.key, self.value)


class ExtensionIndex(Base):
    __tablename__ = 'ext-index'

    ext_id = Column(Integer, Sequence('ei_id_seq'), primary_key=True, nullable=False)
    uuid = Column(String(36), ForeignKey('obj-index.uuid'))
    extension = Column(String(64))

    def __repr__(self):  # pragma: nocover
       return "<ExtensionIndex(uuid='%s', extension='%s')>" % (
                            self.uuid, self.extension)


class ObjectInfoIndex(Base):
    __tablename__ = 'obj-index'

    uuid = Column(String(36), primary_key=True)
    dn = Column(String, index=True)
    _parent_dn = Column(String, index=True)
    _adjusted_parent_dn = Column(String, index=True)
    _type = Column(String(64), index=True)
    _last_modified = Column(DateTime)
    _invisible = Column(Boolean)
    properties = relationship("KeyValueIndex", order_by=KeyValueIndex.key)
    extensions = relationship("ExtensionIndex", order_by=ExtensionIndex.extension)
    search_object = relationship("SearchObjectIndex", back_populates="object")

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
    currently_in_creation = []
    currently_moving = {}
    __search_aid = {}
    last_notification = None
    # notification period in seconds during indexing
    notify_every = 1
    __value_extender = None

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
        orm.configure_mappers()
        Base.metadata.create_all(self.env.getDatabaseEngine("backend-database"))

        # Store DB session
        self.__session = self.env.getDatabaseSession("backend-database")
        self.__value_extender = gosa.backend.objects.renderer.get_renderers()


        # create view
        try:
            # check if extension exists
            if self.__session.execute("SELECT * FROM \"pg_extension\" WHERE extname = 'pg_trgm';").rowcount == 0:
                self.__session.execute("CREATE EXTENSION pg_trgm;")

            view_name = "unique_lexeme"
            # check if view exists
            res = self.__session.execute("SELECT count(*) > 0 as \"exists\" FROM pg_catalog.pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind = 'm' AND n.nspname = 'public' AND c.relname = '%s';" % view_name).first()
            if res[0] is False:
                self.__session.execute("CREATE MATERIALIZED VIEW %s AS SELECT word FROM ts_stat('SELECT so_index.search_vector FROM so_index');" % view_name)
                self.__session.execute("CREATE INDEX words_idx ON %s USING gin(word gin_trgm_ops);" % view_name)
            self.fuzzy = True
        except Exception as e:
            self.log.error("Error creating view for unique word index: %s" % str(e))
            self.__session.rollback()

        # If there is already a collection, check if there is a newer schema available
        schema = self.factory.getXMLObjectSchema(True)
        if self.isSchemaUpdated(schema):
            if self.env.config.get("backend.index", "true").lower() == "false":
                self.log.error("object definitions changed and the index needs to be re-created. Please enable the index in your config file!")
            else:
                self.__session.query(Schema).delete()
                self.__session.query(KeyValueIndex).delete()
                self.__session.query(ExtensionIndex).delete()
                self.__session.query(SearchObjectIndex).delete()
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
        if self.env.config.get("backend.index", "true").lower() == "true":
            import sys
            if hasattr(sys, '_called_from_test'):
                self.sync_index()
            else:
                sobj = PluginRegistry.getInstance("SchedulerService")
                sobj.getScheduler().add_date_job(self.sync_index,
                       datetime.datetime.now() + datetime.timedelta(seconds=1),
                       tag='_internal', jobstore='ram')
        else:
            def finish():
                zope.event.notify(IndexScanFinished())

            sobj = PluginRegistry.getInstance("SchedulerService")
            sobj.getScheduler().add_date_job(finish,
                                             datetime.datetime.now() + datetime.timedelta(seconds=10),
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

    def notify_frontends(self, state, progress=None, step=None):
        e = EventMaker()
        ev = e.Event(e.BackendState(
            e.Type("index"),
            e.State(state),
            e.Progress(str(progress)),
            e.Step(str(step)),
            e.TotalSteps(str(4))
        ))
        event_object = objectify.fromstring(etree.tostring(ev, pretty_print=True).decode('utf-8'))
        SseHandler.notify(event_object, channel="broadcast")

    def sync_index(self):
        # Don't index if someone else is already doing it
        if GlobalLock.exists("scan_index"):
            return

        # Don't run index, if someone else already did until the last
        # restart.
        cr = PluginRegistry.getInstance("CommandRegistry")
        GlobalLock.acquire("scan_index")
        ObjectIndex.importing = True
        updated = 0
        added = 0
        existing = 0
        removed = 0

        try:
            self._indexed = True

            t0 = time.time()
            self.last_notification = time.time()

            def resolve_children(dn):
                self.log.debug("found object '%s'" % dn)
                res = {}

                children = self.factory.getObjectChildren(dn)
                res = {**res, **children}

                for chld in children.keys():
                    res = {**res, **resolve_children(chld)}
                now = time.time()
                if now - self.last_notification > self.notify_every:
                    self.notify_frontends(N_("scanning for objects"), step=1)
                    self.last_notification = now

                return res

            self.log.info("scanning for objects")
            self.notify_frontends(N_("scanning for objects"), step=1)
            res = resolve_children(self.env.base)
            # count by type
            counts = {}
            for o in res.keys():
                if res[o] not in counts:
                    counts[res[o]] = 1
                else:
                    counts[res[o]] += 1

            self.log.debug("Found objects: %s" % counts)
            res[self.env.base] = 'dummy'

            self.log.info("generating object index")
            self.notify_frontends(N_("Generating object index"))

            # Find new entries
            backend_objects = []
            total = len(res)
            current = 0

            for o in sorted(res.keys(), key=len):
                current += 1

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
                    added += 1
                    self.insert(obj, True)

                # Entry is in the database
                else:
                    # OK: already there
                    if obj.modifyTimestamp == last_modified[0]:
                        self.log.debug("found up-to-date object index for %s" % obj.uuid)
                        existing += 1
                    else:
                        self.log.debug("updating object index for %s" % obj.uuid)
                        self.update(obj)
                        updated += 1

                backend_objects.append(obj.uuid)
                del obj

                now = time.time()
                if now - self.last_notification > self.notify_every:
                    self.notify_frontends(N_("Processing object %s/%s" % (current, total)), round(100/total*current), step=2)
                    self.last_notification = now

            self.notify_frontends(N_("%s objects processed" % total), 100)

            # Remove entries that are in the index, but not in any other backends
            self.notify_frontends(N_("removing orphan objects from index"), step=3)
            self.__remove_others(backend_objects)
            # uuids = self.__session.query(~ObjectInfoIndex.uuid.in_(backend_objects)).all()
            # total = len(uuids)
            # current = 0
            # for uuid in uuids:
            #     current += 1
            #     uuid = uuid[0]
            #     self.remove_by_uuid(uuid)
            #     removed += 1
            #     now = time.time()
            #     if now - lastNotification > notifyEvery:
            #         notify_frontends(N_("Deleting object %s/%s" % (current, total)), round(100/total*current))
            #         lastNotification = now

            t1 = time.time()
            self.log.info("processed %d objects in %ds" % (len(res), t1 - t0))
            self.log.info("%s added, %s updated, %s removed, %s are up-to-date" % (added, updated, removed, existing))

        except Exception as e:
            self.log.critical("building the index failed: %s" % str(e))
            import traceback
            traceback.print_exc()

        finally:
            self.post_process()
            self.log.info("index refresh finished")
            self.notify_frontends(N_("Index refresh finished"), 100)

            GlobalLock.release("scan_index")
            zope.event.notify(IndexScanFinished())

    def post_process(self):
        ObjectIndex.importing = False
        self.last_notification = time.time()
        current = 0
        total = len(ObjectIndex.to_be_updated)

        # Some object may have queued themselves to be re-indexed, process them now.
        self.log.info("need to refresh index for %d objects" % total)
        for dn in self.__session.query(ObjectInfoIndex.dn).filter(ObjectInfoIndex.uuid.in_(ObjectIndex.to_be_updated)).all():
            current += 1
            if dn:
                obj = ObjectProxy(dn[0])
                self.update(obj)

                now = time.time()
                if now - self.last_notification > self.notify_every:
                    self.notify_frontends(N_("refreshing object %s/%s" % (current, total)), round(100/total*current), step=4)
                    self.last_notification = now

        ObjectIndex.to_be_updated = []

        self.update_words()

    def index_active(self):  # pragma: nocover
        return self._indexed

    def update_words(self):
        # update unique word list
        if self.fuzzy is True:
            self.__session.execute("REFRESH MATERIALIZED VIEW unique_lexeme;")

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

            if event.reason[0:4] == "post" and _uuid and _dn and change_type and \
                    (change_type != "update" or len(event.changed_props)):

                ev = e.Event(e.ObjectChanged(
                    e.UUID(_uuid),
                    e.DN(_dn),
                    e.ModificationTime(_last_changed.strftime("%Y%m%d%H%M%SZ")),
                    e.ChangeType(change_type)
                ))
                event_string = "<?xml version='1.0'?>\n%s" % etree.tostring(ev, pretty_print=True).decode('utf-8')

                # Validate event
                xml = objectify.fromstring(event_string, PluginRegistry.getEventParser())

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

        # assemble search object
        if data['_type'] in self.__search_aid['mapping']:
            aid = self.__search_aid['mapping'][data['_type']]
            attrs = self.__search_aid['attrs'][data['_type']] if data['_type'] in self.__search_aid['attrs'] else []
            types = [data['_type']]
            types.extend(data["_extensions"])
            # append aliases to search words
            if data['_type'] in self.__search_aid['aliases']:
                types.extend(self.__search_aid['aliases'][data['_type']])

            search_words = [", ".join(data[x]) for x in attrs if x in data and data[x] is not None]
            so = SearchObjectIndex(
                so_uuid=data["_uuid"],
                reverse_parent_dn=','.join([d for d in ldap.dn.explode_dn(data["_parent_dn"], flags=ldap.DN_FORMAT_LDAPV3)[::-1]]),
                title=self.__build_value(aid["title"], data),
                description=self.__build_value(aid["description"], data),
                search=" ".join(search_words),
                types=" ".join(list(set(types)))
            )
            self.__session.add(so)
        self.__session.commit()

        # update word index on change (if indexing is not running currently)
        if not GlobalLock.exists("scan_index"):
            self.update_words()

    def __build_value(self, v, info):
        """
        Fill placeholders in the value to be displayed as "description".
        """
        if not v:
            return None

        if v in info:
            return ", ".join(info[v])

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

    def remove(self, obj):
        self.remove_by_uuid(obj.uuid)

    def __remove_others(self, uuids):
        self.log.debug("removing a bunch of objects")

        self.__session.query(KeyValueIndex).filter(~KeyValueIndex.uuid.in_(uuids)).delete(synchronize_session=False)
        self.__session.query(ExtensionIndex).filter(~ExtensionIndex.uuid.in_(uuids)).delete(synchronize_session=False)
        self.__session.query(SearchObjectIndex).filter(~SearchObjectIndex.so_uuid.in_(uuids)).delete(synchronize_session=False)
        self.__session.query(ObjectInfoIndex).filter(~ObjectInfoIndex.uuid.in_(uuids)).delete(synchronize_session=False)
        self.__session.commit()

    def remove_by_uuid(self, uuid):
        self.log.debug("removing object index for %s" % uuid)

        if self.exists(uuid):
            self.__session.query(KeyValueIndex).filter(KeyValueIndex.uuid == uuid).delete()
            self.__session.query(ExtensionIndex).filter(ExtensionIndex.uuid == uuid).delete()
            self.__session.query(SearchObjectIndex).filter(SearchObjectIndex.so_uuid == uuid).delete()
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
        use_extension = False

        def __make_filter(n):
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
                    elif 'not_in_' in value or 'in_' in value:
                        if hasattr(ObjectInfoIndex, key):
                            attr = getattr(ObjectInfoIndex, key)
                            if 'not_in_' in value:
                                res.append(~attr.in_(value['not_in_']))
                            elif 'in_' in value:
                                res.append(attr.in_(value['in_']))
                        else:
                            in_expr = None
                            if 'not_in_' in value:
                                in_expr = ~KeyValueIndex.value.in_(value['not_in_'])
                            elif 'in_' in value:
                                in_expr = KeyValueIndex.value.in_(value['in_'])
                            sub_query = self.__session.query(KeyValueIndex.uuid).filter(KeyValueIndex.key == key, in_expr).subquery()
                            res.append(ObjectInfoIndex.uuid.in_(sub_query))

                    else:
                        raise IndexException(C.make_error('NOT_SUPPORTED', "base", operator=key))

                elif isinstance(value, list):
                    # implicit or_ in case of lists - hashes cannot have multiple
                    # keys with the same name
                    exprs = []
                    for v in value:
                        # convert integers because we need strings
                        if isinstance(v, int):
                            v = "%s" % v
                        if hasattr(ObjectInfoIndex, key):
                            if "%" in v:
                                if v == "%":
                                    exprs.append(getattr(ObjectInfoIndex, key).like(v))
                                else:
                                    exprs.append(getattr(ObjectInfoIndex, key).ilike(v))
                            else:
                                exprs.append(getattr(ObjectInfoIndex, key) == v)
                        elif key == "extension":
                            use_extension = True
                            exprs.append(ExtensionIndex.extension == v)
                        else:
                            if "%" in v:
                                if v == "%":
                                    sub_query = self.__session.query(KeyValueIndex.uuid). \
                                        filter(and_(KeyValueIndex.key == key, KeyValueIndex.value.like(v))). \
                                        subquery()
                                else:
                                    sub_query = self.__session.query(KeyValueIndex.uuid). \
                                        filter(and_(KeyValueIndex.key == key, KeyValueIndex.value.ilike(v))). \
                                        subquery()
                            else:
                                sub_query = self.__session.query(KeyValueIndex.uuid). \
                                    filter(and_(KeyValueIndex.key == key, KeyValueIndex.value == v)). \
                                    subquery()
                            res.append(ObjectInfoIndex.uuid.in_(sub_query))

                    res.append(or_(*exprs))

                else:
                    # convert integers because we need strings
                    if isinstance(value, int):
                        value = "%s" % value
                    if hasattr(ObjectInfoIndex, key):
                        if "%" in value:
                            res.append(getattr(ObjectInfoIndex, key).ilike(value))
                        else:
                            res.append(getattr(ObjectInfoIndex, key) == value)
                    elif key == "extension":
                        use_extension = True
                        res.append(ExtensionIndex.extension == value)
                    else:
                        if "%" in value:
                            if value == "%":
                                sub_query = self.__session.query(KeyValueIndex.uuid).\
                                    filter(and_(KeyValueIndex.key == key, KeyValueIndex.value.like(value))).\
                                    subquery()
                            else:
                                sub_query = self.__session.query(KeyValueIndex.uuid). \
                                    filter(and_(KeyValueIndex.key == key, KeyValueIndex.value.ilike(value))). \
                                    subquery()
                        else:
                            sub_query = self.__session.query(KeyValueIndex.uuid).\
                                filter(and_(KeyValueIndex.key == key, KeyValueIndex.value == value)).\
                                subquery()
                        res.append(ObjectInfoIndex.uuid.in_(sub_query))

            return res

        # Add query information to be able to search various tables
        _args = __make_filter(node)

        if use_extension:
            args = [ObjectInfoIndex.uuid == ExtensionIndex.uuid]
            args += _args
            return and_(*args)

        return _args

    def search(self, query, properties, options=None):
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
        if options is None:
            options = {}

        q = self.__session.query(ObjectInfoIndex)\
            .options(joinedload(ObjectInfoIndex.properties)) \
            .options(joinedload(ObjectInfoIndex.extensions))\
            .filter(*fltr)

        if 'limit' in options:
            q.limit(options['limit'])

        # try:
        #     self.log.debug(str(q.statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})))
        # except Exception as e:
        #     self.log.error("Error creating SQL string: %s" % str(e))
        #     self.log.debug(str(q))

        try:
            for o in q.all():
                res.append(normalize(o, properties))
        except sqlalchemy.exc.InternalError as e:
            self.log.error(str(e))
            self.__session.rollback()

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
