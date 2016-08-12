#!/usr/bin/python3

import unittest
import zope.event
from gosa.common.event import EventMaker
from gosa.common.events import *
from gosa.common.gjson import dumps


class EventsTestCase(unittest.TestCase):
    def test_EventNotAuthorized(self):
        assert issubclass(EventNotAuthorized, Exception)

    def test_Event(self):
        e = Event("data", "emitter")
        e2 = Event(data="data", emitter="emitter")
        assert e.get_data() == e2.get_data() == "data"
        assert e.get_emitter() == e2.get_emitter() == "emitter"

    def test_ZopeEventConsumer(self):
        e = EventMaker()
        callback = unittest.mock.Mock()
        zec = ZopeEventConsumer(callback=callback)
        event = Event(unittest.mock.MagicMock())
        zope.event.notify(event)
        callback.assert_called_once_with(event.get_data())
        
        callback = unittest.mock.Mock()
        event = Event(e.Event(e.TestEvent))
        zec = ZopeEventConsumer(callback=callback, event_type="TestEvent")
        zope.event.notify(event)
        callback.assert_called_once_with(event.get_data())

    def test_MqttEventConsumer(self):
        schema = '<?xml version="1.0"?>' \
                 '<schema xmlns="http://www.w3.org/2001/XMLSchema" xmlns:e="http://www.gonicus.de/Events" ' \
                 'targetNamespace="http://www.gonicus.de/Events" elementFormDefault="qualified">'\
                 '<include schemaLocation="/home/tobiasb/develop/gosa3/next/backend/src/gosa/backend/data/events/BackendChange.xsd"/>'\
                 '<complexType name="Event">'\
                 '<choice maxOccurs="1" minOccurs="1">'\
                 '<group ref="e:Events"/>'\
                 '</choice>'\
                 '</complexType>'\
                 '<group name="Events">'\
                 '<choice>'\
                 '<element name="BackendChange" type="e:BackendChange"/>'\
                 '</choice>'\
                 '</group>'\
                 '<element name="Event" type="e:Event"/>'\
                 '</schema>'

        with unittest.mock.patch("gosa.common.events.PluginRegistry.getEventSchema", return_value=schema):
            e = EventMaker()
            callback = unittest.mock.Mock()
            event = e.Event(
                e.BackendChange(
                    e.DN("dn"),
                    e.ModificationTime("mod_time"),
                    e.ChangeType("type")
                )
            )
            mec = MqttEventConsumer(callback=callback, event_type="BackendChange")
            payload = dumps({
                "sender_id": None,
                "content": etree.tostring(event, pretty_print=True).decode('utf-8')
            })
            message = unittest.mock.MagicMock()
            message.payload = payload
            message.topic = "%s/events" % Environment.getInstance().domain
            mec.mqtt.get_client().client.on_message(None, None, message)

            args, kwargs = callback.call_args
            assert etree.tostring(args[0], pretty_print=True).decode('utf-8') == etree.tostring(event, pretty_print=True).decode('utf-8')
            PluginRegistry._event_parser = None