# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

"""
The *CommandRegistry* is responsible for knowing what kind of commands
are available for users. It works together with the
:class:`gosa.common.components.registry.PluginRegistry` and inspects
all loaded plugins for methods marked with the
:meth:`gosa.common.components.command.Command` decorator. All available
information like *method path*, *command name*,
*documentation* and *signature* are recorded and are available for users
via the :meth:`gosa.backend.command.CommandRegistry.dispatch` method
(or better with the several proxies) and the CLI.

.. note::

    Please take a look at the :ref:`command index <cindex>` for a list
    of valid commands.

-------
"""
import re
import logging
from datetime import timedelta

from lxml import objectify, etree

import zope
import gettext

from tornado import gen
from tornado.gen import coroutine

from gosa.common.components.mqtt_handler import MQTTHandler
from gosa.common.components.mqtt_proxy import MQTTServiceProxy
from gosa.common.exceptions import ACLException
from pkg_resources import resource_filename #@UnresolvedImport
from threading import Event
from inspect import getargspec, getmembers, ismethod
from zope.interface import implementer
from gosa.common.components import PluginRegistry, ObjectRegistry, Command, no_login_commands
from gosa.common.gjson import loads
from gosa.common.handler import IInterfaceHandler
from gosa.common import Environment
from gosa.common.utils import stripNs, N_
from gosa.common.error import GosaErrorHandler as C
from gosa.common.components import Plugin
from gosa.common.events import Event, EventNotAuthorized
from gosa.backend.exceptions import CommandInvalid, CommandNotAuthorized, MQTTProxyException
from gosa.backend.routes.sse.main import SseHandler


# Global command types
NORMAL = 1
FIRSTRESULT = 2
CUMULATIVE = 4


# Register the errors handled  by us
C.register_codes(dict(
    COMMAND_NO_USERNAME=N_("Calling method '%(method)s' without a valid user session is not permitted"),
    COMMAND_NOT_DEFINED=N_("Method '%(method)s' is not defined"),
    PERMISSION_EXEC=N_("No permission to execute method '%(method)s'"),
    PERMISSION_EVENT=N_("No permission to send event '%(topic)s'"),
    COMMAND_WITHOUT_DOCS=N_("Method '%(method)s' has no documentation")
    ))


@implementer(IInterfaceHandler)
class CommandRegistry(Plugin):
    """
    This class covers the registration and invocation of methods
    imported thru plugins.
    """
    _priority_ = 0
    _target_ = "core"

    objects = {}
    commands = {}

    mqtt = None
    backend_proxy = None

    def __init__(self):
        env = Environment.getInstance()
        self.env = env
        self.log = logging.getLogger(__name__)
        self.log.info("initializing command registry")

    @Command(__help__=N_("Returns the LDAP base"), type="READONLY")
    def getBase(self):
        """
        Returns the LDAP base used by the agent as string

        ``Return``: a string representing the LDAP base
        """
        return self.env.base

    @Command(needsUser=True, __help__=N_("List all methods that are allowed for the given user."), type="READONLY")
    def getAllowedMethods(self, user):
        """
        Lists the all methods that are available in the domain and are allowed for the user.

        ``Return``: list with methods names
        """
        res = []
        acl = PluginRegistry.getInstance("ACLResolver")

        for name, info in self.commands.items():
            if acl.check(user, "%s.%s.%s" % (self.env.domain, "command", name), "x"):
                res.append(name)

        return res

    @Command(__help__=N_("List available methods that are registered on the bus."), type="READONLY")
    def getMethods(self, locale=None):
        """
        Lists the all methods that are available in the domain.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        locale            Translate __help__ strings to the desired language
        ================= ==========================

        ``Return``: dict describing all methods
        """
        res = {}
        for name, info in self.commands.items():

            # Only list local methods
            res[name] = info

            # Adapt to locale if required
            if locale:
                mod = PluginRegistry.getInstance(info['path'].split(".")[0]).get_locale_module()
                t = gettext.translation('messages',
                        resource_filename(mod, "locale"),
                        fallback=True,
                        languages=[locale])
                res[name]['doc'] = t.gettext(info['doc'])

        return res

    @Command(noLoginRequired=True, __help__=N_("List available methods that are allowed without login."), type="READONLY")
    def getNoLoginMethods(self):
        return no_login_commands

    @Command(__help__=N_("Shut down the service."))
    def shutdown(self, force=False):
        """
        In case of HTTP connections, this command will shut down the node you're currently
        logged in.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        force             force global shut down
        ================= ==========================

        ``Return``: True when shutting down
        """
        self.log.debug("received shutdown signal - waiting for threads to terminate")
        PluginRegistry.getInstance('HTTPService').stop()
        return True

    def hasMethod(self, func):
        """
        Check if the desired method is available.

        ========== ============
        Parameter  Description
        ========== ============
        func       method to check for
        ========== ============

        ``Return:`` flag if available or not
        """
        return func in self.commands

    def call(self, func, *arg, **larg):
        """
        *call* can be used to internally call a registered method
        directly. There's no access control happening with this
        method.

        ========== ============
        Parameter  Description
        ========== ============
        func       method to call
        args       ordinary argument list/dict
        ========== ============

        ``Return:`` return value from the method call
        """

        # We pass 'self' as user, to skip acls checks.
        return self.dispatch(self, None, func, *arg, **larg)

    def dispatch(self, user, session_id, func, *arg, **larg):
        """
        The dispatch method will try to call the specified function and
        checks for user.

        Handlers like JSONRPC should use this function to dispatch the real calls.

        ========== ============
        Parameter  Description
        ========== ============
        user       the calling users name
        session_id the calling session id
        func       method to call
        args       ordinary argument list/dict
        ========== ============

        ``Return:`` the real methods result
        """

        # Check for user authentication (if user is 'self' this is an internal call)
        if not user and user != self:
            raise CommandNotAuthorized(C.make_error("COMMAND_NO_USERNAME", method=func))

        # Check if the command is available
        if func not in self.commands:
            if self.env.mode == "proxy":
                # try to execute command on GOsa-backend
                self.log.debug("forward '%s' execution to GOsa backend" % func)
            else:
                raise CommandInvalid(C.make_error("COMMAND_NOT_DEFINED", method=func))

        # Check for permission (if user equals 'self' then this is an internal call)
        if user != self and func not in self.getNoLoginMethods():
            chk_options = dict(zip(self.commands[func]['sig'], arg))
            chk_options.update(larg)
            acl = PluginRegistry.getInstance("ACLResolver")
            if not acl.check(user, "%s.%s.%s" % (self.env.domain, "command", func), "x", options=chk_options):
                raise CommandNotAuthorized(C.make_error("PERMISSION_EXEC", method=func))

        # Convert to list
        arg = list(arg)

        # Check if call is interested in calling user ID, prepend it
        if self.callNeedsUser(func):
            if user != self:
                arg.insert(0, user)
            else:
                arg.insert(0, None)

        # Check if call is interested in calling session ID, prepend it
        if self.callNeedsSession(func):
            index = 1 if self.callNeedsUser(func) else 0
            if user != self:
                arg.insert(index, session_id)
            else:
                arg.insert(index, None)

        # Handle function type (additive, first match, regular)
        (clazz, method) = self.path2method(self.commands[func]['path'])

        method = PluginRegistry.modules[clazz].__getattribute__(method)
        execute_locally = self.env.mode != "proxy" or getattr(method, "type", "READWRITE") != "READWRITE"

        if execute_locally is True:
            self.log.info("executing '%s' locally" % func)
            return method(*arg, **larg)
        else:
            self.log.info("proxying '%s(%s)' call to GOsa backend via %s:%s" % (func, arg, self.mqtt.host, self.mqtt.port))

            if self.callNeedsUser(func):
                larg['__user__'] = arg.pop(0)
            else:
                # always add user to the call (for general ACL checks)
                larg['__user__'] = user
            if self.callNeedsSession(func):
                larg['__session_id__'] = arg.pop(0)

            future = getattr(self.backend_proxy, func)(*arg, **larg)
            return future.result()

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

    def __call_needs(self, func, name):
        if not func in self.commands:
            raise CommandInvalid(C.make_error("COMMAND_NOT_DEFINED", method=func))

        (clazz, method) = self.path2method(self.commands[func]['path'])

        method = PluginRegistry.modules[clazz].__getattribute__(method)
        return getattr(method, name, False)

    def callNeedsUser(self, func):
        """
        Checks if the provided method requires a user parameter.

        ========== ============
        Parameter  Description
        ========== ============
        func       method name
        ========== ============

        ``Return:`` success or failure
        """
        return self.__call_needs(func, "needsUser")

    def callNeedsSession(self, func):
        """
        Checks if the provided method requires a session parameter.

        ========== ============
        Parameter  Description
        ========== ============
        func       method name
        ========== ============

        ``Return:`` success or failure
        """
        return self.__call_needs(func, "needsSession")

    def __del__(self):
        self.log.debug("shutting down command registry")

    def serve(self):
        """
        Start serving the command registry to the outside world. Send
        hello and register event callbacks.
        """

        for clazz in PluginRegistry.modules.values():
            for mname, method in getmembers(clazz):
                if ismethod(method) and hasattr(method, "isCommand"):
                    func = mname

                    # Adjust documentation
                    if not method.__help__:
                        raise CommandInvalid(C.make_error("COMMAND_WITHOUT_DOCS", method=func))

                    doc = re.sub("(\s|\n)+", " ", method.__help__).strip()

                    self.log.debug("registering %s" % func)
                    info = {
                        'name': func,
                        'path': "%s.%s" % (clazz.__class__.__name__, mname),
                        'sig': [] if not getargspec(method).args else getargspec(method).args,
                        'target': clazz.get_target(),
                        'type': getattr(method, "type", NORMAL),
                        'doc': doc,
                        }

                    if 'self' in info['sig']:
                        info['sig'].remove('self')

                    self.commands[func] = info

        if self.env.mode == "proxy":
            # initializing MQTTServiceProxy to GOsa backend
            self.mqtt = MQTTHandler(host=self.env.config.get("backend.mqtt-host"), port=self.env.config.getint("backend.mqtt-port", default=1883))
            queue = '%s/proxy/%s' % (self.env.domain, self.env.uuid)
            self.backend_proxy = MQTTServiceProxy(mqttHandler=self.mqtt, serviceAddress=queue, methods=False)

    @Command(needsUser=True, __help__=N_("Return the current session's user ID."), type="READONLY")
    def getSessionUser(self, user):
        return user

    @Command(needsUser=True, __help__=N_("Send event to the bus."))
    def sendEvent(self, user, data):
        """
        Sends an event to the SSE handler and the zope event bus. Data must be in XML format,
        see :ref:`Events handling <events>` for details.

        ========== ============
        Parameter  Description
        ========== ============
        data       valid event
        ========== ============

        *sendEvent* will indirectly validate the event against the bundled "XSD".
        """

        try:
            event = "<?xml version='1.0'?>\n"

            if isinstance(data, str):
                event += data
            elif isinstance(data, bytes):
                event += data.decode('utf-8')
            else:
                event += etree.tostring(data, pretty_print=True).decode('utf-8')

            # Validate event
            xml = objectify.fromstring(event, PluginRegistry.getEventParser())
            event_type = list(xml.__dict__.keys())[0]
            # If a user was supplied, check if she's authorized...
            if user:
                acl = PluginRegistry.getInstance("ACLResolver")
                topic = ".".join([self.env.domain, 'event', event_type])
                if not acl.check(user, topic, "x"):
                    raise EventNotAuthorized("sending the event '%s' is not permitted" % topic)

            if event_type in ['ObjectChanged', 'Notification', 'ObjectCloseAnnouncement']:
                params = {'channel': 'broadcast'}

                if event_type == "Notification" and xml.Notification.Target.text != "all":
                    params['channel'] = "user.%s" % xml.Notification.Target.text
                if event_type == "ObjectCloseAnnouncement":
                    params['channel'] = "user.%s" % xml.ObjectCloseAnnouncement.Target.text

                SseHandler.notify(xml, **params)

            zope.event.notify(Event(data=xml, emitter=user))

        except etree.XMLSyntaxError as e:
            if self.env:
                self.log.error("event rejected (%s): %s" % (str(e), data))
            raise
