# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
The *ClientCommandRegistry* is responsible for knowing what kind of commands
are available for the client. It works together with the
:class:`gosa.common.components.registry.PluginRegistry` and inspects
all loaded plugins for methods marked with the
:meth:`gosa.common.components.command.Command` decorator. All available
information like *method path*, *command name*, *documentation* and
*signature* are recorded and are available for users
via the :meth:`gosa.agent.plugins.goto.client_service.ClientService.clientDispatch` method
(or better with the several proxies) and the CLI.

-------
"""
import re
import inspect
import logging
from zope.interface import implementer

from gosa.common.handler import IInterfaceHandler
from gosa.common.components import Command, CommandInvalid
from gosa.common.components.registry import PluginRegistry
from gosa.common import Environment


@implementer(IInterfaceHandler)
class ClientCommandRegistry(object):
    """
    This class covers the registration and invocation of methods
    imported thru plugins.
    """
    _priority_ = 2
    commands = {}
    nodes = {}
    proxy = {}

    def __init__(self):
        env = Environment.getInstance()
        log = self.log = logging.getLogger(__name__)
        self.log.debug("initializing command registry")
        self.env = env

        for clazz in PluginRegistry.modules.values():
            for method in clazz.__dict__.values():
                if hasattr(method, "isCommand"):

                    func = method.__name__
                    if not method.__doc__:
                        raise Exception("method '%s' has no documentation" % func)
                    doc = re.sub("(\s|\n)+", " ", method.__doc__).strip()

                    log.debug("registering %s" % func)
                    info = {
                        'path': "%s.%s" % (clazz.__name__, method.__name__),
                        'sig': inspect.getargspec(method).args,
                        'doc': doc,
                        }
                    self.commands[func] = info

    def register(self, func, path, args, sig, doc):
        self.commands[func] = {'path': path, 'sig': sig, 'doc': doc, 'args': args}

    def unregister(self, func):
        del self.commands[func]

    def dispatch(self, func, *arg, **larg):
        """
        The dispatch method will try to call the specified function and
        checks for user and queue. Additionally, it carries the call to
        it's really destination (function types, cumulative results) and
        does some sanity checks.

        Handlers like JSONRPC or AMQP should use this function to
        dispatch the real calls.

        ========== ============
        Parameter  Description
        ========== ============
        func       method to call
        args       ordinary argument list/dict
        ========== ============

        ``Return:`` the real methods result
        """

        # Do we have this method?
        if func in self.commands:
            (clazz, method) = self.path2method(self.commands[func]['path'])
            if 'args' in self.commands[func] and self.commands[func]['args']:
                arg = self.commands[func]['args'] + list(arg)

            return PluginRegistry.modules[clazz].\
                    __getattribute__(method)(*arg, **larg)
        else:
            raise CommandInvalid("no method '%s' available" % func)

    def __del__(self):
        self.log.debug("shutting down command registry")

    @Command()
    def getMethods(self):
        """ List all available client commands """
        return self.commands

    def path2method(self, path):
        """
        Converts the call path (class.method) to the method itself

        ========== ============
        Parameter  Description
        ========== ============
        path       method path including the class
        ========== ============

        ``Return:`` the method name
        """
        return path.rsplit('.')
