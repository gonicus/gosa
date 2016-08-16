# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from gosa.common.utils import stripNs
from lxml import etree

from zope.event import classhandler
from gosa.common import Environment
from gosa.common.components import PluginRegistry
from gosa.common.components.mqtt_handler import MQTTHandler


class BaseEventConsumer(object):

    def __init__(self, callback=None, event_type=None):
        self.__callback = callback
        self.__type = event_type

    def _get_type(self, event):
        return stripNs(event.xpath('/g:Event/*', namespaces={'g': "http://www.gonicus.de/Events"})[0].tag)

    def _process_event(self, event):
        if self.__type is None or self._get_type(event) == self.__type:
            self.__callback(event)


class ZopeEventConsumer(BaseEventConsumer):
    """
    Subscribes to the internal Zope event bus and forwards incoming events to the given callback
    """
    def __init__(self, callback=None, event_type=None):
        super(ZopeEventConsumer, self).__init__(callback, event_type)
        classhandler.handler(Event, self.__process_event)

    def __process_event(self, event):
        super(ZopeEventConsumer, self)._process_event(event.get_data())


class MqttEventConsumer(BaseEventConsumer):
    """
    Subscribes to the external MQTT event topic and forwards incoming events to the given callback
    """
    def __init__(self, callback=None, event_type=None):
        super(MqttEventConsumer, self).__init__(callback, event_type)
        self.mqtt = MQTTHandler()
        self.mqtt.get_client().add_subscription('%s/events' % Environment.getInstance().domain)
        self.mqtt.set_subscription_callback(self.__process_event)

    def __process_event(self, topic, message):
        super(MqttEventConsumer, self)._process_event(etree.fromstring(message, PluginRegistry.getEventParser()))


class Event(object):
    """ Event class used for the zope.event.classhandler """

    def __init__(self, data=None, emitter=None):
        self.__data = data
        self.__emitter = emitter

    def get_data(self):
        return self.__data

    def get_emitter(self):
        return self.__emitter


class EventNotAuthorized(Exception):
    pass
