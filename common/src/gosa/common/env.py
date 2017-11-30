# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
The environment module encapsulates the access of all
central information like logging and configuration management.

You can import it to your own code like this::

   >>> from gosa.common import Environment
   >>> env = Environment.getInstance()

--------
"""
import logging
import platform

from decorator import contextmanager
from sqlalchemy.engine.url import make_url

from gosa.common.config import Config
from gosa.common.utils import dmi_system

try:
    from sqlalchemy.orm import sessionmaker, scoped_session
    from sqlalchemy import create_engine, event
except ImportError: # pragma: nocover
    pass


class Environment:
    """
    The global information container, used as a singleton.
    """
    config = None
    threads = []
    log = None
    id = None
    reset_requested = False
    noargs = False
    domain = None
    __instance = None
    __db = None
    __db_session = None
    __db_factory = None

    def __init__(self):
        # Load configuration
        self.config = Config(config=Environment.config, noargs=Environment.noargs)
        self.log = logging.getLogger(__name__)
        self.id = platform.node()
        self.__db = {}
        self.__db_session = {}
        self.__db_factory = {}

        # Dump configuration
        if self.log.getEffectiveLevel() == logging.DEBUG:
            self.log.debug("configuration dump:")

            for section in self.config.getSections():
                self.log.debug("[%s]" % section)
                items = self.config.getOptions(section)

                for item in items:
                    self.log.debug("%s = %s" % (item, items[item]))

            self.log.debug("end of configuration dump")

        # Load base - we need one
        self.base = self.config.get("core.base")
        self.domain = self.config.get("core.domain", "default")

        self.uuid = self.config.get("core.id", default=None)
        if not self.uuid:
            self.log.warning("system has no id - falling back to configured hardware uuid")
            self.uuid = dmi_system("uuid")

            if not self.uuid:
                self.log.error("system has no id - please configure one in the core section")
                raise Exception("No system id found")

    def requestRestart(self):
        self.log.warning("a component requested an environment reset")
        self.reset_requested = True

    def getDatabaseEngine(self, section, key="database"):
        """
        Return a database engine from the registry.

        ========= ============
        Parameter Description
        ========= ============
        section   name of the configuration section where the config is placed.
        key       optional value for the key where the database information is stored, defaults to *database*.
        ========= ============

        ``Return``: database engine
        """
        index = "%s.%s" % (section, key)

        if not index in self.__db:
            if not self.config.get(index):
                raise Exception("No database connection defined for '%s'!" % index)
            if self.config.get(index).startswith("sqlite://"):
                from sqlalchemy.pool import StaticPool
                self.__db[index] = create_engine(self.config.get(index),
                                                 connect_args={'check_same_thread': False},
                                                 poolclass=StaticPool, encoding="utf-8")
            else:
                self.__db[index] = create_engine(self.config.get(index), encoding="utf-8")

            #TODO: configure engine
            #self.__db[index] = create_engine(self.config.get(index),
            #        pool_size=40, pool_recycle=120, echo=True)

        return self.__db[index]

    # def getDatabaseSession(self, section, key="database"):
    #     """
    #     Return a database session from the pool.
    #
    #     ========= ============
    #     Parameter Description
    #     ========= ============
    #     section   name of the configuration section where the config is placed.
    #     key       optional value for the key where the database information is stored, defaults to *database*.
    #     ========= ============
    #
    #     ``Return``: database session
    #     """
    #     index = "%s.%s" % (section, key)
    #     sql = self.getDatabaseEngine(section, key)
    #     if index not in self.__db_session:
    #         self.__db_session[index] = scoped_session(sessionmaker(autoflush=True, bind=sql))
    #
    #     return self.__db_session[index]()

    def getDatabaseFactory(self, section, key="database"):
        index = "%s.%s" % (section, key)
        if index not in self.__db_factory:
            self.__db_factory[index] = make_session_factory(self.config.get(index))
        return self.__db_factory[index]

    @staticmethod
    def getInstance():
        """
        Act like a singleton and return the
        :class:`gosa.common.env.Environment` instance.

        ``Return``: :class:`gosa.common.env.Environment`
        """
        if not Environment.__instance:
            Environment.__instance = Environment()
        return Environment.__instance

    @staticmethod
    def reset():
        if Environment.__instance:
            Environment.__instance = None

###########################################
# Parts from tornado_sqlalchemy 0.3.3
###########################################


class SessionFactory(object):
    """SessionFactory is a wrapper around the functions that SQLAlchemy
    provides. The intention here is to let the user work at the session level
    instead of engines and connections.

    :param database_url: Database URL
    :param pool_size: Connection pool size
    :param use_native_unicode: Enable/Disable native unicode support. This is
    only used in case the driver is psycopg2.
    :param engine_events: List of (name, listener_function) tuples to subscribe
    to engine events
    :param session_events: List of (name, listener_function) tuples to
    subscribe to session events
    """

    def __init__(self, database_url, pool_size=None, use_native_unicode=True,
                 engine_events=None, session_events=None):
        self._database_url = make_url(database_url)
        self._pool_size = pool_size
        self._engine_events = engine_events
        self._session_events = session_events
        self._use_native_unicode = use_native_unicode

        self._engine = None
        self._factory = None

        self._setup()

    def _setup(self):
        kwargs = {}
        if self._database_url.get_driver_name() == 'postgresql':
            kwargs['use_native_unicode'] = self._use_native_unicode

        if self._pool_size is not None:
            kwargs['pool_size'] = self._pool_size

        self._engine = create_engine(self._database_url, **kwargs)

        if self._engine_events:
            for (name, listener) in self._engine_events:
                event.listen(self._engine, name, listener)

        self._factory = sessionmaker()
        self._factory.configure(bind=self._engine)

    def make_session(self):
        session = self._factory()

        if self._session_events:
            for (name, listener) in self._session_events:
                event.listen(session, name, listener)

        return session

    @property
    def engine(self):
        return self._engine


def make_session_factory(database_url,
                         pool_size=None,
                         use_native_unicode=True,
                         engine_events=None,
                         session_events=None):
    return SessionFactory(database_url, pool_size, use_native_unicode,
                          engine_events, session_events)


class SessionMixin(object):
    @contextmanager
    def make_session(self):
        factory = Environment.getInstance().getDatabaseFactory("backend-database")

        if not factory:
            raise MissingFactoryError()

        try:
            session = factory.make_session()

            yield session
        except:
            session.rollback()
            raise
        else:
            session.commit()
        finally:
            session.close()


class MissingFactoryError(Exception):
    pass