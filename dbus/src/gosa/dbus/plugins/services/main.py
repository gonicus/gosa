# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""

.. _dbus-service:

GOsa D-Bus System Service Plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Allows to manage systemd service units (PowerOff and Reboot are also available).

"""
import dbus.service
import logging
from os.path import basename
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.dbus import get_system_bus
import re
import subprocess


class ServiceException(Exception):
    """
    Exception thrown for general service failures.
    """
    pass


class NotAServiceException(ServiceException):
    """
    Exception thrown for unit_ids which do not end with ".service"
    """
    pass

class NoSuchServiceException(ServiceException):
    """
    Exception thrown for unknown services
    """
    pass


class DBusUnixServiceHandler(dbus.service.Object, Plugin):
    """

    The gosa-dbus system-service-plugin allows to manage services
    running on the client side with systemd.

    A few of the systemd dbus-methods are wrapped.
    Service units can be started, stopped etc.
    PowerOff, Halt and Reboot are also possible.

    """

    log = None
    env = None
    systembus = None

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/org/gosa/service')
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.systembus = dbus.SystemBus()
        systemd_obj = self.systembus.get_object("org.freedesktop.systemd1", "/org/freedesktop/systemd1")
        self.systemd = dbus.Interface(systemd_obj, "org.freedesktop.systemd1.Manager")

    def service_action(self, unit_id, method):
        if not unit_id.endswith(".service"):
            raise NotAServiceException()
        ret = method(unit_id, "replace") # "replace" is default in systemctl, too
        return ret != None

    @dbus.service.method('org.gosa', in_signature='s', out_signature='i')
    def start_service(self, unit_id):
        """
        Starts a systemd service unit
        """
        return self.service_action(unit_id, self.systemd.StartUnit)

    @dbus.service.method('org.gosa', in_signature='s', out_signature='i')
    def stop_service(self, unit_id):
        """
        Stops a systemd service unit
        """
        return self.service_action(unit_id, self.systemd.StopUnit)

    @dbus.service.method('org.gosa', in_signature='s', out_signature='i')
    def restart_service(self, unit_id):
        """
        Restarts a systemd service unit
        """
        return self.service_action(unit_id, self.systemd.RestartUnit)

    @dbus.service.method('org.gosa', in_signature='s', out_signature='i')
    def reload_service(self, unit_id):
        """
        Reloads a systemd service unit
        """
        return self.service_action(unit_id, self.systemd.ReloadUnit)

    @dbus.service.method('org.gosa', in_signature='s', out_signature='i')
    def reload_or_restart_service(self, unit_id):
        """
        Reloads or restarts a systemd service unit
        """
        return self.service_action(unit_id, self.systemd.ReloadOrRestartUnit)

    @dbus.service.method('org.gosa', in_signature='s', out_signature='i')
    def reload_or_try_restart_service(self, unit_id):
        """
        Reloads or try restarts a systemd service unit
        """
        return self.service_action(unit_id, self.systemd.ReloadOrTryRestartUnit)

    @dbus.service.method('org.gosa', in_signature='ssi')
    def kill_service(self, unit_id, who, signal_id):
        """
        Kills processes of a systemd service unit
        """
        if not unit_id.endswith(".service"):
            raise NotAServiceException()
        self.systemd.KillUnit(unit_id, who, signal_id)

    @dbus.service.method('org.gosa', in_signature='s', out_signature='a{sas}')
    def get_service(self, unit_id):
        """
        Returns status information for the given service.
        """
        if not unit_id.endswith(".service"):
            raise NotAServiceException()
        services = self.get_services()
        if not unit_id in services:
            raise NoSuchServiceException("unknown service %s" % unit_id)

        return services[unit_id]

    @dbus.service.method('org.gosa', out_signature='a{sa{sas}}')
    def get_services(self):
        """
        Returns status information for all services.
        """
        services = {}
        units = self.systemd.ListUnits()
        for unit in units:
            if not unit[0].endswith(".service"):
                continue
            services[unit[0]] = {"running": ["True" if unit[4] == "running" else "False"]}
        return services

    @dbus.service.method('org.gosa')
    def reboot(self):
        self.systemd.Reboot()
    @dbus.service.method('org.gosa')
    def poweroff(self):
        self.systemd.PowerOff()
    @dbus.service.method('org.gosa')
    def halt(self):
        self.systemd.Halt()
