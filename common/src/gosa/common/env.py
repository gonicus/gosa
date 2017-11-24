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

import os

from gosa.common.config import Config
from gosa.common.utils import dmi_system

try:
    from sqlalchemy.orm import sessionmaker, scoped_session, exc
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

    def __init__(self):
        # Load configuration
        self.config = Config(config=Environment.config, noargs=Environment.noargs)
        self.log = logging.getLogger(__name__)
        self.id = platform.node()
        self.__db = {}
        self.__db_session = {}

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

                @event.listens_for(self.__db[index], "connect")
                def connect(dbapi_connection, connection_record):
                    connection_record.info['pid'] = os.getpid()

                @event.listens_for(self.__db[index], "checkout")
                def checkout(dbapi_connection, connection_record, connection_proxy):
                    pid = os.getpid()
                    if connection_record.info['pid'] != pid:
                        connection_record.connection = connection_proxy.connection = None
                        raise exc.DisconnectionError(
                            "Connection record belongs to pid %s, "
                            "attempting to check out in pid %s" %
                            (connection_record.info['pid'], pid)
                        )

            #TODO: configure engine
            #self.__db[index] = create_engine(self.config.get(index),
            #        pool_size=40, pool_recycle=120, echo=True)

        return self.__db[index]

    def getDatabaseSession(self, section, key="database"):
        """
        Return a database session from the pool.

        ========= ============
        Parameter Description
        ========= ============
        section   name of the configuration section where the config is placed.
        key       optional value for the key where the database information is stored, defaults to *database*.
        ========= ============

        ``Return``: database session
        """
        index = "%s.%s" % (section, key)
        sql = self.getDatabaseEngine(section, key)
        if index not in self.__db_session:
            self.__db_session[index] = scoped_session(sessionmaker(autoflush=True, bind=sql))

        return self.__db_session[index]()

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
