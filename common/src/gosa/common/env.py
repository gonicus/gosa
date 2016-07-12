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
from gosa.common.config import Config
try:
    from sqlalchemy.orm import sessionmaker, scoped_session
    from sqlalchemy import create_engine
except ImportError: # pragma: nocover
    pass


class Environment:
    """
    The global information container, used as a singleton.
    """
    config = None
    log = None
    reset_requested = False
    noargs = False
    domain = "gosa"
    __instance = None
    __db = None
    __db_session = None

    def __init__(self):
        # Load configuration
        self.config = Config(config=Environment.config, noargs=Environment.noargs)
        self.log = logging.getLogger(__name__)
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
            if self.config.get(index) == "sqlite:///:memory:":
                from sqlalchemy.pool import StaticPool
                self.__db[index] = create_engine(self.config.get(index),
                                                 connect_args={'check_same_thread': False},
                                                 poolclass=StaticPool)
            else:
                self.__db[index] = create_engine(self.config.get(index))

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
        :class:`clacks.common.env.Environment` instance.

        ``Return``: :class:`clacks.common.env.Environment`
        """
        if not Environment.__instance:
            Environment.__instance = Environment()
        return Environment.__instance

    @staticmethod
    def reset():
        if Environment.__instance:
            Environment.__instance = None
