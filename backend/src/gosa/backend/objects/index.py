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
import multiprocessing
import sys
import re
import traceback
from multiprocessing.pool import Pool
from urllib.parse import urlparse

import ldap
import sqlalchemy
from multiprocessing import RLock
from passlib.hash import bcrypt
from requests import HTTPError
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import CreateTable
from sqlalchemy.sql.ddl import DropTable
from sqlalchemy_searchable import make_searchable, search
from sqlalchemy_utils import TSVectorType

import gosa
from gosa.backend.components.httpd import get_server_url, get_internal_server_url
from gosa.backend.objects.backend.back_foreman import ForemanBackendException
from gosa.backend.utils import BackendTypes
from gosa.common.env import declarative_base, make_session
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
from gosa.common.mqtt_connection_state import BusClientAvailability
from gosa.common.utils import N_
from gosa.common.handler import IInterfaceHandler
from gosa.common.components import Command, Plugin, PluginRegistry, JSONServiceProxy
from gosa.common.error import GosaErrorHandler as C, GosaException
from gosa.backend.objects import ObjectFactory, ObjectProxy, ObjectChanged
from gosa.backend.exceptions import FilterException, IndexException, ProxyException, ObjectException
from gosa.backend.lock import GlobalLock
from sqlalchemy.orm import relationship, subqueryload
from sqlalchemy import Column, String, Integer, Boolean, Sequence, DateTime, ForeignKey, or_, and_, not_, func, orm, \
    JSON, Enum
from gosa.backend.routes.system import State

Base = declarative_base()
make_searchable(Base.metadata)


# Register the errors handled  by us
C.register_codes(dict(
    OBJECT_EXISTS=N_("Object with UUID %(uuid)s already exists"),
    OBJECT_NOT_FOUND=N_("Cannot find object %(id)s"),
    INDEXING=N_("Index rebuild in progress - try again later"),
    NOT_SUPPORTED=N_("Requested search operator %(operator)s is not supported"),
    NO_MASTER_BACKEND_FOUND=N_("No master backend found"),
    NO_MASTER_BACKEND_CONNECTION=N_("connection to GOsa backend failed"),
    NO_BACKEND_CREDENTIALS=N_("Please add valid backend credentials to you configuration (core.backend-user, core.backend-key)"),
    DELAYED_UPDATE_FOR_NON_DIRTY_OBJECT=N_("Trying to add a delayed update to a non-dirty object (%(topic)s)")
))


class Schema(Base):
    __tablename__ = 'schema'

    type = Column(String, primary_key=True)
    hash = Column(String(32))

    def __repr__(self):  # pragma: nocover
       return "<Schema(type='%s', hash='%s')>" % (self.type, self.hash)


class SearchObjectIndex(Base):
    __tablename__ = "so_index"
    so_uuid = Column(String(36), ForeignKey('obj-index.uuid'), primary_key=True)
    reverse_parent_dn = Column(String, index=True)
    title = Column(String)
    description = Column(String)
    search = Column(String)
    types = Column(String)
    search_vector = Column(TSVectorType('title', 'description', 'search', 'types',
                                        weights={'title': 'A', 'types': 'D', 'description': 'C', 'search': 'B'},
                                        regconfig='pg_catalog.simple'
                                        ))
    object = relationship("ObjectInfoIndex", uselist=False, back_populates="search_object")

    def __repr__(self):  # pragma: nocover

        return "<SearchObjectIndex(so_uuid='%s', reverse_parent_dn='%s', title='%s', description='%s')>" % \
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
    _master_backend = Column(String)
    properties = relationship("KeyValueIndex", order_by=KeyValueIndex.key)
    extensions = relationship("ExtensionIndex", order_by=ExtensionIndex.extension)
    search_object = relationship("SearchObjectIndex", back_populates="object")

    def __repr__(self):  # pragma: nocover
       return "<ObjectInfoIndex(uuid='%s', dn='%s', _parent_dn='%s', _adjusted_parent_dn='%s', _type='%s', _last_modified='%s', _invisible='%s', _master_backend='%s')>" % (
                            self.uuid, self.dn, self._parent_dn, self._adjusted_parent_dn, self._type, self._last_modified, self._invisible, self._master_backend)


class RegisteredBackend(Base):
    __tablename__ = "registered-backends"
    uuid = Column(String(36), primary_key=True, nullable=False)
    password = Column(String(300), nullable=False)
    url = Column(String)
    type = Column(Enum(BackendTypes))

    def __init__(self, uuid, password, url="", type=BackendTypes.unknown):
        self.uuid = uuid
        self.password = bcrypt.encrypt(password)
        self.url = url
        self.type = type

    def validate_password(self, password):
        return bcrypt.verify(password, self.password)

    def __repr__(self):  # pragma: nocover
        return "<RegisteredBackend(uuid='%s', password='%s', url='%s', type='%s')>" % \
               (self.uuid, self.password, self.url, self.type)


class OpenObject(Base):
    __tablename__ = "open-objects"

    ref = Column(String(36), primary_key=True, nullable=False)
    uuid = Column(String(36), nullable=True)
    oid = Column(String)
    data = Column(JSON)
    backend_uuid = Column(String, ForeignKey('registered-backends.uuid'))
    backend = relationship("RegisteredBackend")
    created = Column(DateTime)
    last_interaction = Column(DateTime)
    user = Column(String)
    session_id = Column(String)

    def __repr__(self):  # pragma: nocover
        return "<OpenObject(ref='%s', uuid='%s', oid='%s', data='%s', backend='%s', created='%s', last_interaction='%s', user='%s', session_id='%s')>" % \
               (self.ref, self.uuid, self.oid, self.data, self.backend, self.created, self.last_interaction, self.user, self.session_id)


class UserSession(Base):
    __tablename__ = "user-sessions"

    sid = Column(String(36), primary_key=True, nullable=False)
    user = Column(String)
    dn = Column(String)
    last_used = Column(DateTime)
    auth_state = Column(Integer)

    def __repr__(self):
        return "<UserSession(sid='%s', user='%s', dn='%s', auth_state='%s', last_used='%s')>" % \
               (self.sid, self.user, self.dn, self.auth_state, self.last_used)


class Cache(Base):
    __tablename__ = "cache"

    key = Column(String, primary_key=True)
    data = Column(JSON)
    time = Column(DateTime)

    def __repr__(self):
        return "<Cache(key='%s',data='%s',time='%s')" % (self.key, self.data, self.time)


@compiles(DropTable, "postgresql")
def _compile_drop_table(element, compiler, **kwargs):
    return compiler.visit_drop_table(element) + " CASCADE"


class IndexScanFinished():  # pragma: nocover
    pass

class IndexSyncFinished():  # pragma: nocover
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
    _priority_ = 20
    _target_ = 'core'
    _indexed = False
    _post_process_job = None
    importing = False
    to_be_updated = []
    # objects that a currently created (stored in the backend but not in the database yet)
    currently_in_creation = []
    # objects that are have been changes (changes not in database yet)
    __dirty = {}
    currently_moving = {}
    __search_aid = {}
    last_notification = None
    # notification period in seconds during indexing
    notify_every = 1
    __value_extender = None
    _acl_resolver = None

    procs = multiprocessing.cpu_count()

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
        self.lock = RLock()

    def serve(self):
        # Configure database for the index
        orm.configure_mappers()

        engine = self.env.getDatabaseEngine("backend-database")
        Base.metadata.bind = engine
        Base.metadata.create_all()

        self.__value_extender = gosa.backend.objects.renderer.get_renderers()

        self._acl_resolver = PluginRegistry.getInstance("ACLResolver")

        if self.env.mode == "backend":
            with make_session() as session:

                # create view
                try:
                    # check if extension exists
                    if session.execute("SELECT * FROM \"pg_extension\" WHERE extname = 'pg_trgm';").rowcount == 0:
                        session.execute("CREATE EXTENSION pg_trgm;")

                    if session.execute("SELECT * FROM \"pg_extension\" WHERE extname = 'fuzzystrmatch';").rowcount == 0:
                        session.execute("CREATE EXTENSION fuzzystrmatch;")

                    view_name = "unique_lexeme"
                    # check if view exists
                    res = session.execute("SELECT count(*) > 0 as \"exists\" FROM pg_catalog.pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind = 'm' AND n.nspname = 'public' AND c.relname = '%s';" % view_name).first()
                    if res[0] is False:
                        session.execute("CREATE MATERIALIZED VIEW %s AS SELECT word FROM ts_stat('SELECT so_index.search_vector FROM so_index');" % view_name)
                        session.execute("CREATE INDEX words_idx ON %s USING gin(word gin_trgm_ops);" % view_name)
                    self.fuzzy = True
                except Exception as e:
                    self.log.error("Error creating view for unique word index: %s" % str(e))
                    session.rollback()

                try:
                    current_db_hash = session.query(Schema).filter(Schema.type == 'database').one_or_none()
                except:
                    current_db_hash = None

                # check DB schema
                tables = [Schema.__table__, KeyValueIndex.__table__, ExtensionIndex.__table__,
                          SearchObjectIndex.__table__, ObjectInfoIndex.__table__, RegisteredBackend.__table__]
                sql = ""
                for table in tables:
                    statement = CreateTable(table)
                    sql += str(statement.compile(dialect=postgresql.dialect()))

                md5s = hashlib.md5()
                md5s.update(sql.encode('utf-8'))
                md5sum = md5s.hexdigest()
                db_recreated = False
                schema = self.factory.getXMLObjectSchema(True)

                if current_db_hash is None or current_db_hash.hash != md5sum:
                    # Database schema has changed -> re-create
                    self.log.info("database schema has changed, dropping object tables")
                    session.commit()
                    Base.metadata.drop_all()
                    Base.metadata.create_all()
                    self.log.info("created new database tables")
                    db_schema = Schema(type='database', hash=md5sum)
                    session.add(db_schema)
                    session.commit()
                    # enable indexing
                    self.env.backend_index = True
                    db_recreated = True

                else:

                    # If there is already a collection, check if there is a newer schema available
                    if self.isSchemaUpdated(schema):
                        session.query(Schema).filter(Schema.type == 'objects').delete()
                        session.query(KeyValueIndex).delete()
                        session.query(ExtensionIndex).delete()
                        session.query(SearchObjectIndex).delete()
                        session.query(ObjectInfoIndex).delete()
                        session.query(OpenObject).delete()  # delete references to backends
                        session.query(RegisteredBackend).delete()
                        self.log.info('object definitions changed, dropped old object index')
                        # enable indexing
                        self.env.backend_index = True

                # Create the initial schema information if required
                if not session.query(Schema).filter(Schema.type == 'objects').one_or_none():
                    self.log.info('created schema')
                    md5s = hashlib.md5()
                    md5s.update(schema)
                    md5sum = md5s.hexdigest()

                    schema = Schema(type='objects', hash=md5sum)
                    session.add(schema)
                    session.commit()

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

        # store core_uuid/core_key into DB
        if hasattr(self.env, "core_uuid"):
            if self.env.mode == "backend":
                with make_session() as session:

                    if db_recreated is False:
                        tables_to_recreate = [UserSession.__table__, OpenObject.__table__, RegisteredBackend.__table__]

                        for table in tables_to_recreate:
                            table.drop(engine)

                        Base.metadata.create_all(tables=tables_to_recreate)

                    rb = RegisteredBackend(
                        uuid=self.env.core_uuid,
                        password=self.env.core_key,
                        url=get_server_url(),
                        type=BackendTypes.active_master
                    )
                    session.add(rb)
                    session.commit()
            else:
                self.registerProxy()

        # Schedule index sync
        if self.env.backend_index is True and self.env.mode == 'backend':
            if not hasattr(sys, '_called_from_test'):
                sobj = PluginRegistry.getInstance("SchedulerService")
                sobj.getScheduler().add_date_job(self.syncIndex,
                                                 datetime.datetime.now() + datetime.timedelta(seconds=1),
                                                 tag='_internal', jobstore='ram')
        else:
            def finish():
                zope.event.notify(IndexScanFinished())
                zope.event.notify(IndexSyncFinished())
                State.system_state = "ready"

            sobj = PluginRegistry.getInstance("SchedulerService")
            sobj.getScheduler().add_date_job(finish,
                                             datetime.datetime.now() + datetime.timedelta(seconds=10),
                                             tag='_internal', jobstore='ram')

    def registerProxy(self, backend_uuid=None):
        if self.env.mode == "proxy":
            # register on the current master
            with make_session() as session:
                # get any other registered backend
                if backend_uuid is None:
                    master_backend = session.query(RegisteredBackend) \
                        .filter(RegisteredBackend.uuid != self.env.core_uuid,
                                RegisteredBackend.type == BackendTypes.active_master).first()
                else:
                    master_backend = session.query(RegisteredBackend) \
                        .filter(RegisteredBackend.uuid == backend_uuid,
                                RegisteredBackend.type == BackendTypes.active_master).first()

                if master_backend is None:
                    raise GosaException(C.make_error("NO_MASTER_BACKEND_FOUND"))

                # Try to log in with provided credentials
                url = urlparse("%s/rpc" % master_backend.url)
                connection = '%s://%s%s' % (url.scheme, url.netloc, url.path)
                proxy = JSONServiceProxy(connection)

                if self.env.config.get("core.backend-user") is None or self.env.config.get("core.backend-key") is None:
                    raise GosaException(C.make_error("NO_BACKEND_CREDENTIALS"))

                # Try to log in
                try:
                    if not proxy.login(self.env.config.get("core.backend-user"), self.env.config.get("core.backend-key")):
                        raise GosaException(C.make_error("NO_MASTER_BACKEND_CONNECTION"))
                    else:
                        proxy.registerBackend(self.env.core_uuid,
                                              self.env.core_key, get_internal_server_url(),
                                              BackendTypes.proxy)
                except HTTPError as e:
                    if e.code == 401:
                        raise GosaException(C.make_error("NO_MASTER_BACKEND_CONNECTION"))
                    else:
                        self.log.error("Error: %s " % str(e))
                        raise GosaException(C.make_error("NO_MASTER_BACKEND_CONNECTION"))

                # except Exception as e:
                #     self.log.error("Error: %s " % str(e))
                #     raise GosaException(C.make_error("NO_MASTER_BACKEND_CONNECTION"))

    def stop(self):
        if self.__handle_events in zope.event.subscribers:
            zope.event.subscribers.remove(self.__handle_events)

    def mark_as_dirty(self, obj):
        """
        Marks an object as "dirty". Dirty objects are currently being persisted to their backends (aka committed).
        :param obj:
        :type obj: gosa.backend.proxy.ObjectProxy
        :return:
        """
        if not self.is_dirty(obj.uuid):
            self.__dirty[obj.uuid] = {"obj": obj, "updates": []}
            self.log.info("marked %s (%s) as dirty (%s)" % (obj.uuid, obj.dn, self.__dirty))

    def is_dirty(self, uuid):
        """
        Check if an object identified by UUID is marked as "dirty".
        :param uuid: UUID ob the object to check
        :type uuid: str
        :return: True if "dirty"
        """
        return uuid in self.__dirty

    def get_dirty_objects(self):
        return self.__dirty

    def add_delayed_update(self, obj, update, inject=False):
        """
        Add a delayed update for an object that is currently being committed (marked "dirty").
        This update will be processed after the ongoing commit has been completed.
        :param obj: The object to apply the update to
        :type obj: gosa.backend.proxy.ObjectProxy
        :param update: updated data that can be processed by :meth:`gosa.backend.proxy.ObjectProxy.apply_update`
        :type update: dict
        """
        if not self.is_dirty(obj.uuid):
            self.log.warning("Trying to add a delayed update to a non-dirty object '%s'" % obj.uuid)
            obj.apply_update(update)
            obj.commit()
            return

        self.log.info("adding delayed update to %s (%s)" % (obj.uuid, obj.dn))
        self.__dirty[obj.uuid]["updates"].append({
            "inject": inject,
            "data": update
        })

    def unmark_as_dirty(self, id):
        """
        removes the "dirty" mark for the object and processes the delayed updates
        :param id: UUID of the Object to unmark or ObjectProxy instance
        :type id: str|ObjectProxy
        """
        if isinstance(id, ObjectProxy):
            uuid = id.uuid
        else:
            uuid = id
        if self.is_dirty(uuid):
            obj = self.__dirty[uuid]['obj']
            if len(self.__dirty[uuid]['updates']) > 0:
                # freshly open the object
                entry = self.__dirty[uuid]
                new_obj = ObjectProxy(entry["obj"].dn)
                for update in entry["updates"]:
                    if update["inject"] is True:
                        self.log.info("injecting %s to %s" % (update["data"], obj.uuid))
                        new_obj.inject_backend_data(update["data"], force_update=True)
                    else:
                        self.log.info("applying %s to %s" % (update["data"], obj.uuid))
                        new_obj.apply_update(update["data"])
                del self.__dirty[uuid]
                new_obj.commit()
            else:
                del self.__dirty[uuid]

            self.log.info("unmarked %s (%s) as dirty (%s)" % (obj.uuid, obj.dn, self.__dirty))

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
        if not hasattr(sys, '_called_from_test'):
            if self._post_process_job:
                sched.reschedule_date_job(self._post_process_job, next_run)
            else:
                self._post_process_job = sched.add_date_job(self._post_process_by_timer, next_run, tag='_internal', jobstore="ram", )

        # Resolve dn from uuid if needed
        with make_session() as session:
            if not dn:
                dn = session.query(ObjectInfoIndex.dn).filter(ObjectInfoIndex.uuid == _uuid).one_or_none()

            # Modification
            if change_type == "modify":

                # Get object
                obj = self._get_object(dn)
                if not obj:
                    return

                # Check if the entry exists - if not, maybe let create it
                entry = session.query(ObjectInfoIndex.dn).filter(
                    or_(
                        ObjectInfoIndex.uuid == _uuid,
                        func.lower(ObjectInfoIndex.dn) == func.lower(dn)
                    )).one_or_none()
                if entry:
                    self.update(obj, session=session)

                else:
                    self.insert(obj, session=session)

            # Add
            if change_type == "add":

                # Get object
                obj = self._get_object(dn)
                if not obj:
                    return

                self.insert(obj, session=session)

            # Delete
            if change_type == "delete":
                self.log.info("object has changed in backend: indexing %s" % dn)
                self.log.warning("external delete might not take care about references")
                if _uuid is not None:
                    self.remove_by_uuid(_uuid, session=session)
                else:
                    obj = self._get_object(dn)
                    if obj is None:
                        # lets see if we can find a UUID for the deleted DN
                        uuid = session.query(ObjectInfoIndex.uuid).filter(func.lower(ObjectInfoIndex.dn) == func.lower(dn)).one_or_none()
                        if uuid is not None:
                            self.remove_by_uuid(uuid)
                    else:
                        self.remove(obj)

            # Move
            if change_type in ['modrdn', 'moddn']:
                # Check if the entry exists - if not, maybe let create it
                entry = session.query(ObjectInfoIndex).filter(
                    or_(
                        ObjectInfoIndex.uuid == _uuid,
                        func.lower(ObjectInfoIndex.dn) == func.lower(dn)
                    )).one_or_none()

                if new_dn is not None and new_dn[-1:] == ",":
                    # only new RDN received, get parent from db
                    if entry is not None:
                        new_dn = new_dn + entry._parent_dn
                    else:
                        self.log.error('DN modification event received: could not get parent DN from existing object to complete the new DN')

                # Get object
                obj = self._get_object(new_dn)
                if not obj:
                    return

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
            elif _uuid is not None:
                ev = e.Event(e.ObjectChanged(
                    e.UUID(_uuid),
                    e.DN(dn),
                    e.ModificationTime(_last_changed.strftime("%Y%m%d%H%M%SZ")),
                    e.ChangeType(event_change_type)
                ))
            else:
                ev = e.Event(e.ObjectChanged(
                    e.DN(dn),
                    e.ModificationTime(_last_changed.strftime("%Y%m%d%H%M%SZ")),
                    e.ChangeType(event_change_type)
                ))

            event = "<?xml version='1.0'?>\n%s" % etree.tostring(ev, pretty_print=True).decode('utf-8')

            # Validate event
            xml = objectify.fromstring(event, PluginRegistry.getEventParser())

            SseHandler.notify(xml, channel="broadcast")

            if hasattr(sys, '_called_from_test'):
                self.post_process()

    def get_last_modification(self, backend='LDAP'):
        with make_session() as session:
            res = session.query(ObjectInfoIndex._last_modified)\
                .filter(ObjectInfoIndex._master_backend == backend)\
                .order_by(ObjectInfoIndex._last_modified.desc())\
                .limit(1)\
                .one_or_none()

            if res is not None:
                return res[0]
        return None

    def _post_process_by_timer(self):
        self._post_process_job = None
        self.post_process()

    def _get_object(self, dn):
        try:
            obj = ObjectProxy(dn)

        except (ProxyException, ldap.NO_SUCH_OBJECT) as e:
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

        with make_session() as session:
            stored_md5sum = session.query(Schema.hash).filter(Schema.type == 'objects').one_or_none()
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

    @Command(__help__=N_('Start index synchronizing from an optional root-DN'))
    def syncIndex(self, base=None):
        State.system_state = "indexing"
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
        total = 0
        index_successful = False
        t0 = time.time()
        if base is None:
            start_dn = self.env.base
        else:
            start_dn = base
        try:
            self._indexed = True

            self.last_notification = time.time()

            self.log.info("scanning for objects")
            self.notify_frontends(N_("scanning for objects"), step=1)
            with Pool(processes=self.procs) as pool:
                children = self.factory.getObjectChildren(start_dn)
                result = pool.starmap_async(resolve_children, [(dn,) for dn in children.keys()])
                while not result.ready():
                    self.notify_frontends(N_("scanning for objects"), step=1)
                    self.last_notification = time.time()
                    time.sleep(self.notify_every)

                res = children
                for r in result.get():
                    res = {**res, **r}

            # count by type
            counts = {}
            for o in res.keys():
                if res[o] not in counts:
                    counts[res[o]] = 1
                else:
                    counts[res[o]] += 1

            self.log.info("Found objects: %s" % counts)
            res[self.env.base] = 'dummy'

            self.log.info("generating object index")
            self.notify_frontends(N_("Generating object index"))

            # Find new entries
            backend_objects = []
            total = len(res)
            oids = sorted(res.keys(), key=len)

            with Pool(processes=self.procs) as pool:
                result = pool.starmap_async(process_objects, [(oid,) for oid in oids], chunksize=1)
                while not result.ready():
                    now = time.time()
                    current = total-result._number_left
                    self.notify_frontends(N_("Processing object %s/%s" % (current, total)), round(100/total*current), step=2)
                    self.last_notification = now
                    time.sleep(self.notify_every)

                for r, uuid, to_be_updated in result.get():
                    backend_objects.append(uuid)
                    ObjectIndex.to_be_updated.extend(to_be_updated)
                    if r == "added":
                        added += 1
                    elif r == "existing":
                        existing += 1
                    elif r == "updated":
                        updated += 1

            self.notify_frontends(N_("%s objects processed" % total), 100, step=2)

            # Remove entries that are in the index, but not in any other backends
            if base is None:
                self.notify_frontends(N_("removing orphan objects from index"), step=3)
                with make_session() as session:
                    removed = self.__remove_others(backend_objects, session=session)
            else:
                removed = 0

            self.log.info("%s added, %s updated, %s removed, %s are up-to-date" % (added, updated, removed, existing))
            index_successful = True

        except Exception as e:
            self.log.critical("building the index failed: %s" % str(e))
            traceback.print_exc()

        finally:
            if index_successful is True:
                self.post_process()
                self.log.info("index refresh finished")
                self.notify_frontends(N_("Index refresh finished"), 100, step=4)

                GlobalLock.release("scan_index")
                t1 = time.time()
                self.log.info("processed %d objects in %ds" % (total, t1 - t0))
                # notify others that the index scan is done, they now can do own sync processed
                zope.event.notify(IndexScanFinished())
                # now the index is really ready and up-to-date
                zope.event.notify(IndexSyncFinished())
                State.system_state = "ready"
            else:
                raise IndexException("Error creating index, please restart.")

    def post_process(self):
        ObjectIndex.importing = False
        self.last_notification = time.time()
        uuids = list(set(ObjectIndex.to_be_updated))
        ObjectIndex.to_be_updated = []
        total = len(uuids)

        # Some object may have queued themselves to be re-indexed, process them now.
        self.log.info("need to refresh index for %d objects" % total)

        with Pool(processes=self.procs) as pool:
            result = pool.starmap_async(post_process, [(uuid,) for uuid in uuids], chunksize=1)
            while not result.ready():
                now = time.time()
                current = total-result._number_left
                if GlobalLock.exists("scan_index"):
                    self.notify_frontends(N_("Refreshing object %s/%s" % (current, total)), round(100/total*current), step=4)
                self.last_notification = now
                time.sleep(self.notify_every)

        if len(ObjectIndex.to_be_updated):
            self.post_process()

        self.update_words()

    def index_active(self):  # pragma: nocover
        return self._indexed

    def update_words(self, session=None):
        if session is None:
            with make_session() as session:
                self._update_words(session)
        else:
            self._update_words(session)

    def _update_words(self, session):
        # update unique word list
        if self.fuzzy is True:

            try:
                session.execute("REFRESH MATERIALIZED VIEW unique_lexeme;")
            except Exception as e:
                session.rollback()
                raise e

    def __handle_events(self, event, retried=0):
        if GlobalLock.exists("scan_index"):
            return

        if isinstance(event, objectify.ObjectifiedElement):
            self.__backend_change_processor(event)

        elif isinstance(event, ObjectChanged):
            change_type = None
            _uuid = event.uuid
            _dn = None
            _last_changed = datetime.datetime.now()

            # Try to find the affected DN
            with make_session() as session:
                e = session.query(ObjectInfoIndex).filter(ObjectInfoIndex.uuid == _uuid).one_or_none()
                if e:

                    # New pre-events don't have a dn. Just skip is in this case...
                    if hasattr(e, 'dn'):
                        _dn = e.dn
                        if e._last_modified is not None:
                            _last_changed = e._last_modified
                    else:
                        _dn = "not known yet"

                if event.reason == "post object remove":
                    self.log.debug("removing object index for %s (%s)" % (_uuid, _dn))
                    self.remove_by_uuid(_uuid, session=session)
                    change_type = "remove"

                if event.reason == "pre object move":
                    self.log.debug("starting object movement from %s to %s" % (_dn, event.dn))
                    self.currently_moving[_dn] = event.dn

                try:
                    if event.reason == "post object move":
                        self.log.debug("updating object index for %s (%s)" % (_uuid, _dn))
                        obj = ObjectProxy(event.dn, skip_value_population=True)
                        self.update(obj, session=session)
                        _dn = obj.dn
                        change_type = "move"
                        if event.orig_dn in self.currently_moving:
                            del self.currently_moving[event.orig_dn]

                    if event.reason == "post object create":
                        self.log.debug("creating object index for %s (%s)" % (_uuid, _dn))
                        obj = ObjectProxy(event.dn, skip_value_population=True)
                        self.insert(obj, session=session)
                        _dn = obj.dn
                        change_type = "create"

                    if event.reason == "post object update":
                        self.log.debug("updating object index for %s (%s)" % (_uuid, _dn))
                        if not event.dn and _dn != "not known yet":
                            event.dn = _dn
                        obj = ObjectProxy(event.dn, skip_value_population=True)
                        self.update(obj, session=session)
                        change_type = "update"
                except ForemanBackendException as e:
                    if e.response.status_code == 404:
                        self.log.info("Foreman object %s (%s) not available yet, skipping index update."
                                      % (_uuid, _dn))
                        # do nothing else as foreman will send some kind of event, when the object becomes available
                    else:
                        raise e

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

        elif isinstance(event, BusClientAvailability):
            backend_registry = PluginRegistry.getInstance("BackendRegistry")
            if event.type == "proxy":
                # entering proxies are not handled, because they register themselves with credentials vie JSONRPC
                if event.state == "leave":
                    self.log.debug("unregistering proxy: %s" % event.client_id)
                    backend_registry.unregisterBackend(event.client_id)
            elif event.type == "backend":
                if event.state == "ready":
                    self.log.debug("new backend announced: %s" % event.client_id)
                    if self.env.mode == "proxy":
                        # register ourselves to this backend
                        self.registerProxy(event.client_id)

    def insert(self, obj, skip_base_check=False, session=None):
        if session is not None:
            self._insert(obj, session, skip_base_check=skip_base_check)
        else:
            with make_session() as session:
                self._insert(obj, session, skip_base_check=skip_base_check)

    def _insert(self, obj, session, skip_base_check=False):
        if not skip_base_check:
            pdn = session.query(ObjectInfoIndex.dn).filter(ObjectInfoIndex.dn == obj.get_parent_dn()).one_or_none()

            # No parent?
            if not pdn:
                self.log.debug("ignoring object that has no base in the current index: " + obj.dn)
                return

            parent = self._get_object(obj.get_parent_dn())
            if not parent.can_host(obj.get_base_type()):
                self.log.debug("ignoring object that is not relevant for the index: " + obj.dn)
                return

        self.log.debug("creating object index for %s (%s)" % (obj.uuid, obj.dn))

        uuid = session.query(ObjectInfoIndex.uuid).filter(ObjectInfoIndex.uuid == obj.uuid).one_or_none()
        if uuid:
            raise IndexException(C.make_error('OBJECT_EXISTS', "base", uuid=obj.uuid))

        with self.lock:
            self.__save(obj.asJSON(True), session=session)

    def __save(self, data, session=None):
        if self.env.mode == "proxy":
            self.log.error("GOsa proxy is not allowed to write anything to the database")

        if session is not None:
            self.__session_save(data, session)
        else:
            with make_session() as session:
                self.__session_save(data, session)

    def __session_save(self, data, session):

        # Assemble object index object
        oi = ObjectInfoIndex(
            uuid=data["_uuid"],
            dn=data["dn"],
            _type=data["_type"],
            _parent_dn=data["_parent_dn"],
            _adjusted_parent_dn=data["_adjusted_parent_dn"],
            _invisible=data["_invisible"],
            _master_backend=data["_master_backend"]
        )

        if '_last_changed' in data:
            oi._last_modified = datetime.datetime.fromtimestamp(data["_last_changed"])

        session.add(oi)

        # Assemble extension index objects
        for ext in data["_extensions"]:
            ei = ExtensionIndex(uuid=data["_uuid"], extension=ext)
            session.add(ei)

        # Assemble key value index objects
        for key, value in data.items():

            # Skip meta information and DN
            if key.startswith("_") or key == "dn":
                continue

            if isinstance(value, list):
                for v in value:
                    kvi = KeyValueIndex(uuid=data["_uuid"], key=key, value=v)
                    session.add(kvi)
            else:
                kvi = KeyValueIndex(uuid=data["_uuid"], key=key, value=value)
                session.add(kvi)

        # assemble search object
        if data['_type'] in self.__search_aid['mapping']:
            aid = self.__search_aid['mapping'][data['_type']]
            attrs = self.__search_aid['attrs'][data['_type']] if data['_type'] in self.__search_aid['attrs'] else []
            types = [data['_type']]
            types.extend(data["_extensions"])
            # append aliases to search words
            for type in types[:]:
                if type in self.__search_aid['aliases']:
                    types.extend(self.__search_aid['aliases'][type])

            for ext in data["_extensions"]:
                if ext in self.__search_aid['mapping']:
                    aid.update(self.__search_aid['mapping'][ext])
                if ext in self.__search_aid['attrs']:
                    attrs.extend(self.__search_aid['attrs'][ext])

            attrs = list(set(attrs))
            search_words = [", ".join(data[x]) for x in attrs if x in data and data[x] is not None]
            so = SearchObjectIndex(
                so_uuid=data["_uuid"],
                reverse_parent_dn=','.join([d for d in ldap.dn.explode_dn(data["_parent_dn"], flags=ldap.DN_FORMAT_LDAPV3)[::-1]]),
                title=self.__build_value(aid["title"], data),
                description=self.__build_value(aid["description"], data),
                search=" ".join(search_words),
                types=" ".join(list(set(types)))
            )
            session.add(so)

        session.commit()

        # update word index on change (if indexing is not running currently)
        if not GlobalLock.exists("scan_index"):
            self.update_words(session=session)

        self.unmark_as_dirty(data["_uuid"])

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

    def remove(self, obj, session=None):
        self.remove_by_uuid(obj.uuid, session=session)

    def __remove_others(self, uuids, session=None):
        if session is not None:
            return self.__session_remove_others(uuids, session)
        else:
            with make_session() as session:
                return self.__session_remove_others(uuids, session)

    def __session_remove_others(self, uuids, session):
        self.log.debug("removing a bunch of objects")

        session.query(KeyValueIndex).filter(~KeyValueIndex.uuid.in_(uuids)).delete(synchronize_session=False)
        session.query(ExtensionIndex).filter(~ExtensionIndex.uuid.in_(uuids)).delete(synchronize_session=False)
        session.query(SearchObjectIndex).filter(~SearchObjectIndex.so_uuid.in_(uuids)).delete(synchronize_session=False)
        removed = session.query(ObjectInfoIndex).filter(~ObjectInfoIndex.uuid.in_(uuids)).delete(synchronize_session=False)
        session.commit()
        return removed

    def remove_by_uuid(self, uuid, session=None):
        if session is not None:
            self.__remove_by_uuid(uuid, session)
        else:
            with make_session() as session:
                self.__remove_by_uuid(uuid, session)

    def __remove_by_uuid(self, uuid, session):
        self.log.debug("removing object index for %s" % uuid)

        if self.exists(uuid, session=session):
            session.query(KeyValueIndex).filter(KeyValueIndex.uuid == uuid).delete()
            session.query(ExtensionIndex).filter(ExtensionIndex.uuid == uuid).delete()
            session.query(SearchObjectIndex).filter(SearchObjectIndex.so_uuid == uuid).delete()
            session.query(ObjectInfoIndex).filter(ObjectInfoIndex.uuid == uuid).delete()
            session.commit()

    def update(self, obj, session=None):
        if session is not None:
            self.__update(obj, session)
        else:
            with make_session() as session:
                self.__update(obj, session)

    def __update(self, obj, session):
        # Gather information

        current = obj.asJSON(True)
        old_dn = session.query(ObjectInfoIndex.dn).filter(ObjectInfoIndex.uuid == obj.uuid).one_or_none()
        if not old_dn:
            raise IndexException(C.make_error('OBJECT_NOT_FOUND', "base", id=obj.uuid))
        old_dn = old_dn[0]

        # Remove old entry and insert new
        with self.lock:
            self.remove_by_uuid(obj.uuid, session=session)
            self.__save(current, session=session)

        # Has the entry been moved?
        if current['dn'] != old_dn:

            # Adjust all ParentDN entries of child objects
            res = session.query(ObjectInfoIndex).filter(
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

                oi = session.query(ObjectInfoIndex).filter(ObjectInfoIndex.uuid == o_uuid).one()
                oi.dn = n_dn
                oi._parent_dn = n_parent
                oi._adjusted_parent_dn = n_adjusted_parent

                session.commit()

    @Command(__help__=N_("Check if an object with the given UUID exists."))
    def exists(self, uuid, session=None):
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
        if session is not None:
            return session.query(ObjectInfoIndex.uuid).filter(ObjectInfoIndex.uuid == uuid).one_or_none() is not None
        else:
            with make_session() as session:
                return session.query(ObjectInfoIndex.uuid).filter(ObjectInfoIndex.uuid == uuid).one_or_none() is not None

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

    def _make_filter(self, node, session):
        use_extension = False

        def __make_filter(n, session):
            nonlocal use_extension

            res = []

            for key, value in n.items():
                if isinstance(value, dict):

                    # Maintain certain key words
                    if key == "and_":
                        res.append(and_(*__make_filter(value, session)))
                    elif key == "or_":
                        res.append(or_(*__make_filter(value, session)))
                    elif key == "not_":
                        res.append(not_(*__make_filter(value, session)))
                    elif 'not_in_' in value or 'in_' in value:
                        if key == "extension":
                            use_extension = True
                            if 'not_in_' in value:
                                res.append(~ExtensionIndex.extension.in_(value['not_in_']))
                            elif 'in_' in value:
                                res.append(ExtensionIndex.extension.in_(value['in_']))

                        elif hasattr(ObjectInfoIndex, key):
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
                            sub_query = session.query(KeyValueIndex.uuid).filter(KeyValueIndex.key == key, in_expr).subquery()
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
                            if key == "*":
                                sub_query = search(session.query(SearchObjectIndex.so_uuid), v, sort=True, regconfig='simple').subquery()
                            elif "%" in v:
                                if v == "%":
                                    sub_query = session.query(KeyValueIndex.uuid). \
                                        filter(and_(KeyValueIndex.key == key, KeyValueIndex.value.like(v))). \
                                        subquery()
                                else:
                                    sub_query = session.query(KeyValueIndex.uuid). \
                                        filter(and_(KeyValueIndex.key == key, KeyValueIndex.value.ilike(v))). \
                                        subquery()
                            else:
                                sub_query = session.query(KeyValueIndex.uuid). \
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
                        if key == "*":
                            sub_query = search(session.query(SearchObjectIndex.so_uuid), value, sort=True, regconfig='simple').subquery()
                        elif "%" in value:
                            if value == "%":
                                sub_query = session.query(KeyValueIndex.uuid). \
                                    filter(and_(KeyValueIndex.key == key, KeyValueIndex.value.like(value))). \
                                    subquery()
                            else:
                                sub_query = session.query(KeyValueIndex.uuid). \
                                    filter(and_(KeyValueIndex.key == key, KeyValueIndex.value.ilike(value))). \
                                    subquery()
                        else:
                            sub_query = session.query(KeyValueIndex.uuid). \
                                filter(and_(KeyValueIndex.key == key, KeyValueIndex.value == value)). \
                                subquery()
                        res.append(ObjectInfoIndex.uuid.in_(sub_query))

            return res

        # Add query information to be able to search various tables
        _args = __make_filter(node, session)

        if use_extension:
            args = [ObjectInfoIndex.uuid == ExtensionIndex.uuid]
            args += _args
            return and_(*args)

        return _args

    def get_extensions(self, uuid):
        """ return the list of active extensions for the given uuid-object as store in the db """
        with make_session() as session:
            q = session.query(ExtensionIndex).filter(ExtensionIndex.uuid == uuid)
            return [e.extension for e in q.all()]

    def search(self, query, properties, options=None, session=None):
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
        if session is None:
            with make_session() as session:
                return self._session_search(session, query, properties, options=options)
        else:
            return self._session_search(session, query, properties, options=options)

    def _session_search(self, session, query, properties, options=None):
        res = []
        fltr = self._make_filter(query, session)

        def normalize(data, resultset=None, so_props=None):
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

            # get data from SearchObjectIndex (e.g. title, description)
            if so_props is not None and len(so_props) > 0 and len(data.search_object) > 0:
                for prop in so_props:
                    _res[prop] = [getattr(data.search_object[0], prop)]

            # Clean the result set?
            if resultset:
                for key in [_key for _key in _res if not _key in resultset.keys() and _key[0:1] != "_"]:
                    _res.pop(key, None)

            return _res
        if options is None:
            options = {}

        q = session.query(ObjectInfoIndex) \
            .options(subqueryload(ObjectInfoIndex.properties)) \
            .options(subqueryload(ObjectInfoIndex.extensions))

        # check if we need something from the searchObject
        so_props = None
        if properties is not None:
            so_props = [x for x in properties if hasattr(SearchObjectIndex, x)]
            if len(so_props) > 0:
                q = q.options(subqueryload(ObjectInfoIndex.search_object))
        q = q.filter(*fltr)

        if 'limit' in options:
            q.limit(options['limit'])

        # self.log.info(print_query(q))

        try:
            for o in q.all():
                res.append(normalize(o, properties, so_props=so_props))
        except sqlalchemy.exc.InternalError as e:
            self.log.error(str(e))
            session.rollback()

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
        if self._acl_resolver.isAdmin(user):
            return entry
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
        if user:
            topic = "%s.objects.%s.attributes.%s" % (self.env.domain, object_type, attr)
            return self._acl_resolver.check(user, topic, "r", base=object_dn)
        else:
            return True


# needs to be top level to be picklable
def process_objects(o):
    res = None
    index = PluginRegistry.getInstance("ObjectIndex")
    with make_session() as inner_session:

        if o is None:
            return None, None, ObjectIndex.to_be_updated

        # Get object
        try:
            obj = ObjectProxy(o)

        except Exception as e:
            index.log.warning("not indexing %s: %s" % (o, str(e)))
            return res, None, ObjectIndex.to_be_updated

        # Check for index entry
        last_modified = inner_session.query(ObjectInfoIndex._last_modified).filter(ObjectInfoIndex.uuid == obj.uuid).one_or_none()

        # Entry is not in the database
        if not last_modified:
            index.insert(obj, True, session=inner_session)
            res = "added"

        # Entry is in the database
        else:
            # OK: already there
            if obj.modifyTimestamp == last_modified[0]:
                index.log.debug("found up-to-date object index for %s (%s)" % (obj.uuid, obj.dn))
                res = "existing"
            else:
                index.log.debug("updating object index for %s (%s)" % (obj.uuid, obj.dn))
                index.update(obj, session=inner_session)
                res = "updated"

        uuid = obj.uuid
        del obj
        return res, uuid, ObjectIndex.to_be_updated


def post_process(uuid):
    index = PluginRegistry.getInstance("ObjectIndex")
    with make_session() as inner_session:
        if uuid:
            try:
                obj = ObjectProxy(uuid)
                index.update(obj, session=inner_session)
                return True

            except Exception as e:
                index.log.warning("not post-processing %s: %s" % (uuid, str(e)))
                traceback.print_exc()
                return False

    return False


def resolve_children(dn):
    index = PluginRegistry.getInstance("ObjectIndex")
    index.log.debug("found object '%s'" % dn)
    res = {}

    children = index.factory.getObjectChildren(dn)
    res = {**res, **children}

    for chld in children.keys():
        res = {**res, **resolve_children(chld)}

    return res


@implementer(IInterfaceHandler)
class BackendRegistry(Plugin):
    _target_ = 'core'
    _priority_ = 99

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    @Command(__help__=N_("Register a backend to allow MQTT access"))
    def registerBackend(self, uuid, password, url=None, type=BackendTypes.unknown):
        with make_session() as session:
            query = session.query(RegisteredBackend).filter(or_(RegisteredBackend.uuid == uuid,
                                                                RegisteredBackend.url == url))
            if query.count() > 0:
                # delete old entries
                query.delete()

            rb = RegisteredBackend(
                uuid=uuid,
                password=password,
                url=url,
                type=type
            )
            session.add(rb)
            session.commit()

    @Command(__help__=N_("Unregister a backend from MQTT access"))
    def unregisterBackend(self, uuid):
        with make_session() as session:
            backend = session.query(RegisteredBackend).filter(RegisteredBackend.uuid == uuid).one_or_none()
            if backend is not None:
                session.delete(backend)
                session.commit()

    def check_auth(self, uuid, password):
        if hasattr(self.env, "core_uuid") and self.env.core_uuid == uuid and self.env.core_key == password:
            return True

        with make_session() as session:
            backend = session.query(RegisteredBackend).filter(RegisteredBackend.uuid == uuid).one_or_none()
            if backend is not None:
                return backend.validate_password(password)
        return False

    def get_type(self, uuid):
        # do not use DB if we want to identify ourselves
        if hasattr(self.env, "core_uuid") and self.env.core_uuid == uuid:
            return BackendTypes.proxy if self.env.mode == "proxy" else BackendTypes.active_master

        with make_session() as session:
            try:
                res = session.query(RegisteredBackend.type).filter(RegisteredBackend.uuid == uuid).one_or_none()
                return res[0] if res is not None else None
            except Exception as e:
                self.log.error('Error querying backend type from db: %s' % str(e))
                return None

