#!/usr/bin/python3

import unittest
import zope.event
from gosa.common.events import *

class EventsTestCase(unittest.TestCase):
    def test_EventNotAuthorized(self):
        assert issubclass(EventNotAuthorized, Exception)
    def test_Event(self):
        e = Event("data", "emitter")
        e2 = Event(data="data", emitter="emitter")
        assert e.get_data() == e2.get_data() == "data"
        assert e.get_emitter() == e2.get_emitter() == "emitter"
    def test_ZopeEventConsumer(self):
        callback = unittest.mock.Mock()
        zec = ZopeEventConsumer(callback=callback)
        event = Event(unittest.mock.MagicMock())
        zope.event.notify(event)
        callback.assert_called_once_with(event.get_data())
        
        callback = unittest.mock.Mock()
        event = Event(unittest.mock.MagicMock())
        tag = "sometag"
        event.get_data().getchildren()[0].tag = tag
        zec = ZopeEventConsumer(callback=callback, type="sometag")
        zope.event.notify(event)
        callback.assert_called_once_with(event.get_data())
        
        callback = unittest.mock.Mock()
        event = Event(unittest.mock.MagicMock())
        tag = "{someNs}sometag"
        event.get_data().getchildren()[0].tag = tag
        zec = ZopeEventConsumer(callback=callback, type="sometag")
        zope.event.notify(event)
        callback.assert_called_once_with(event.get_data())
        
        callback = unittest.mock.Mock()
        event = Event(unittest.mock.MagicMock())
        tag = "{someNs}sometag"
        event.get_data().getchildren()[0].tag = tag
        zec = ZopeEventConsumer(callback=callback, type="someothertag")
        zope.event.notify(event)
        assert callback.call_count == 0
