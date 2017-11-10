# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
.. _client-session:

Session trigger
===============

To. Do.
"""

import pwd
import dbus
import zope.event
from gosa.common.components import Plugin
from gosa.common.components import Command
from gosa.common.components.registry import PluginRegistry
from gosa.common.components.dbus_runner import DBusRunner
from gosa.common import Environment
from gosa.common.event import EventMaker
from zope.interface import implementer
from gosa.common.handler import IInterfaceHandler
from gosa.client.event import Resume


@implementer(IInterfaceHandler)
class SessionKeeper(Plugin):
    """
    Utility class that contains methods needed to handle WakeOnLAN
    functionality.
    """

    _priority_ = 99
    _target_ = 'session'
    __sessions = {}
    __callbacks = []
    active = False

    def __init__(self):
        env = Environment.getInstance()
        self.env = env
        self.__dr = DBusRunner.get_instance()
        self.__bus = None

        # Register for resume events
        zope.event.subscribers.append(self.__handle_events)

    @Command()
    def getSessions(self):
        """ Return the list of active sessions """
        return self.__sessions

    def serve(self):
        self.__bus = self.__dr.get_system_bus()

        # Trigger session update
        self.__update_sessions()

        # register a signal receiver
        self.__bus.add_signal_receiver(self.event_handler,
            dbus_interface="org.freedesktop.login1.Manager")

        # Trigger session update
        self.__update_sessions()

    def stop(self):
        if self.__bus:
            self.__bus.remove_signal_receiver(self.event_handler,
                dbus_interface="org.freedesktop.login1.Manager")

    def registerCallback(self, callback):
        self.__callbacks.append(callback)

    def __handle_events(self, event):
        if isinstance(event, Resume):
            self.__update_sessions()

    def event_handler(self, msg_string, dbus_message):
        self.__update_sessions()

        for callback in self.__callbacks:
            #pylint: disable=E1102
            callback(dbus_message.get_member(), msg_string)

    def __update_sessions(self):
        obj = self.__bus.get_object("org.freedesktop.login1",
            "/org/freedesktop/login1")
        interface = dbus.Interface(obj, "org.freedesktop.login1.Manager")
        sessions = {}

        for uid_number, uid, user_path in interface.ListUsers():
            if int(uid_number) > int(self.env.config.get('user.min-uid', "1000")):
                sessions[str(uid_number)] = {
                    "uid": str(uid),
                }
        self.__sessions = sessions
        self.sendSessionNotification()

    def sendSessionNotification(self):
        # Build event
        mqtt = PluginRegistry.getInstance("MQTTClientHandler")
        e = EventMaker()
        more = set([x['uid'] for x in self.__sessions.values()])
        more = map(e.Name, more)
        info = e.Event(
            e.UserSession(
                e.Id(self.env.uuid),
                e.User(*more)))

        mqtt.send_event(info)
