# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
The configuration module is the central place where the GOsa configuration
can be queried. Using the configuration module requires the presence of the
GOsa configuration file - commonly ``/etc/gosa/config`` and the subdirectory
``/etc/gosa/config.d``. All these configurations will be merged into one
'virtual' configuration so that certain packages can provide their own config
file without knowing how to read it.

Additionally to reading the configuration file, it merges that information
with potential command line parameters.

Here is an example on how to use the common module::

    >>> from gosa.common import Environment
    >>> cfg = Environment.getInstance().config
    >>> cfg.get('ldap.base')
    dc=gonicus,dc=de

If no configuration is present, the system will raise a
:class:`gosa.common.config.ConfigNoFile` exception.

-----------
"""
import os
import re
import sys
import configparser
import logging
import logging.config
import getpass
import pwd
import grp
from argparse import ArgumentParser
from gosa.common import __version__ as VERSION
from io import StringIO


class ConfigNoFile(Exception):
    """
    Exception to inform about non existing or not accessible
    configuration files.
    """
    pass


class Config(object):
    """
    Construct a new Config object using the provided configuration file
    and parse the ``sys.argv`` information.

    ========= ============
    Parameter Description
    ========= ============
    config    Path to the configuration file.
    noargs    Don't parse ``sys.argv`` information
    ========= ============
    """
    __registry = {'core': {
                    'pidfile': '/var/run/gosa/gosa.pid',
                    'profile': 0,
                    'umask': 0o002,
                }
            }
    __configKeys = None
    __modified = False

    def __init__(self, config=None, noargs=False):
        if not config:
            config = os.environ.get('GOSA_CONFIG_DIR') or "/etc/gosa"

        # Load default user name for config parsing
        self.__registry['core']['config'] = config

        if os.path.exists(os.path.join('/var', 'lib', 'gosa')):
            self.__registry['core']['user-config'] = os.path.join('/var', 'lib', 'gosa')
        else:
            self.__registry['core']['user-config'] = config

        self.__noargs = noargs
        # settings can be changed via the GUI, in order to identify then
        # we hold them additionally in an separate structure
        self.__user_config = None

        # Load file configuration
        if not self.__noargs:
            self.__parseCmdOptions()
        self.__parseCfgOptions()

        user = getpass.getuser()
        userHome = pwd.getpwnam(user).pw_dir
        group = grp.getgrgid(pwd.getpwnam(user).pw_gid).gr_name

        self.__registry['core']['user'] = user
        self.__registry['core']['group'] = group

    def __parseCmdOptions(self):
        parser = ArgumentParser(usage="%(prog)s - the gosa daemon")
        parser.add_argument("--version", action='version', version=VERSION)

        parser.add_argument("-c", "--config", dest="config",
                          default=os.environ.get('GOSA_CONFIG_DIR') or "/etc/gosa",
                          help="read configuration from DIRECTORY [%(default)s]",
                          metavar="DIRECTORY")
        options, argv = parser.parse_known_args()

        items = options.__dict__
        self.__registry['core'].update(dict([(k, items[k]) for k in items if items[k] != None]))

    def getBaseDir(self):
        return self.__registry['core']['config']

    def getSections(self):
        """
        Return the list of available sections of the ini file. There should be at
        least 'core' available.

        ``Return``: list of sections
        """
        return self.__registry.keys()

    def getOptions(self, section):
        """
        Return the list of provided option names in the specified section of the
        ini file.

        ========= ============
        Parameter Description
        ========= ============
        str       section name in the ini file
        ========= ============

        ``Return``: list of options
        """
        return self.__registry[section.lower()]

    def get(self, path, default=None, use_user_config=True, method="get"):
        """
        *get* allows dot-separated access to the configuration structure.
        If the desired value is not defined, you can specify a default
        value.

        For example, if you want to access the *id* option located
        in the section *[core]*, the path is:

            core.id

        ========= ============
        Parameter Description
        ========= ============
        path      dot-separated path to the configuration option
        default   default value if the desired option is not set
        ========= ============

        ``Return``: value or default
        """
        parts = path.split(".")
        section = parts[0]
        key = parts[1]

        # override with user config if exists
        if use_user_config is True and self.__user_config and self.__user_config.has_section(section) and self.__user_config.has_option(\
                section, key):
            return getattr(self.__user_config, method)(section, key)

        tmp = self.__registry
        try:
            for pos in path.split("."):
                tmp = tmp[pos.lower()]
            return tmp

        except KeyError:
            pass

        return default

    def getfloat(self, path, default=None, use_user_config=True):
        return self.get(path, default, use_user_config, "getfloat")

    def set(self, path, value):
        """
        *set* allows dot-separated changing of configuration settings.
        These values are store in and read from a separate user-config file.

        :param path: dot-separated path to the configuration option
        :param value: the value to set
        """
        if self.__user_config is None:
            return

        parts = path.split(".")
        section = parts[0]
        key = parts[1]

        # change value in the user_registry
        try:
            if self.get(path, use_user_config=False) != value:
                self.__user_config.set(section, key, value)
            elif self.__user_config.get(section, key) != value:
                # return to unchanged value -> do not override
                self.__user_config.remove_option(section, key)
                if len(self.__user_config.options(section)) == 0:
                    self.__user_config.remove_section(section)

        except configparser.NoSectionError:
            self.__user_config.add_section(section)
            self.__user_config.set(section, key, value)

        if path == "logger_gosa.level":
            # apply changed log level
            logging.getLogger("gosa").setLevel(getattr(logging, value))

        elif path == "formatter_console.format":
            try:
                fmt = logging.Formatter(value)
                hldr = logging.getLogger("gosa").handlers[0]
                hldr.setFormatter(fmt)
            except Exception as e:
                logging.error(e)


    def save(self):
        """ save the settings in the main config file """
        if self.__user_config is not None:
            main_config_file = os.path.join(self.get('core.user-config'), "user-config")
            with open(main_config_file, 'w') as f:
                self.__user_config.write(f)

    def __getCfgFiles(self, cdir):
        conf = re.compile(r"^[a-z0-9_.-]+\.conf$", re.IGNORECASE)
        try:
            return [os.path.join(cdir, cfile)
                for cfile in os.listdir(cdir)
                if os.path.isfile(os.path.join(cdir, cfile)) and conf.match(cfile)]
        except OSError:
            return []

    def __parseCfgOptions(self):
        # Is there a configuration available?
        configDir = self.get('core.config')
        configFiles = self.__getCfgFiles(os.path.join(configDir, "config.d"))
        configFiles.insert(0, os.path.join(configDir, "config"))

        config = configparser.RawConfigParser()
        filesRead = config.read(configFiles)

        # Bail out if there's no configuration file
        if not filesRead:
            raise ConfigNoFile("No usable configuration file (%s/config) found!" % configDir)

        # Walk thru core configuration values and push them into the registry
        for section in config.sections():
            if not section in self.__registry:
                self.__registry[section] = {}
            self.__registry[section].update(config.items(section))

        if not hasattr(sys, "_called_from_test") or getattr(sys, "_called_from_test") is False:
            # do not use this in tests
            self.__user_config = configparser.RawConfigParser()
            # read the settings changed via gui client
            if os.path.exists(os.path.join(self.get('core.user-config'), "user-config")):
                filesRead = self.__user_config.read(os.path.join(self.get('core.user-config'), "user-config"))
                if not filesRead:
                    raise ConfigNoFile("No usable GUI configuration file (%s/user-config) found!" % configDir)

        # Initialize the logging module on the fly
        try:
            if self.__user_config is not None:
                for section in self.__user_config.sections():
                    for option, value in self.__user_config.items(section):
                        config.set(section, option, value)

            tmp = StringIO()
            config.write(tmp)
            tmp2 = StringIO(tmp.getvalue())
            logging.config.fileConfig(tmp2)

        except configparser.NoSectionError:
            logging.basicConfig(level=logging.ERROR, format='%(asctime)s (%(levelname)s): %(message)s')
