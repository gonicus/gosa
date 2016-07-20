#!/usr/bin/python3

import unittest
import datetime
from gosa.common.components.scheduler.triggers.simple import *

class SimpleTriggerTestCase(unittest.TestCase):
    def test_simpleTrigger(self):
        t = SimpleTrigger("2016-12-12")
        assert t.get_next_fire_time(datetime.datetime(2016,12,11)) == datetime.datetime(2016,12,12)
        assert str(t) == "date[%s]" % str(datetime.datetime(2016,12,12))
        assert repr(t) == "<SimpleTrigger (run_date=%s)>" % repr(datetime.datetime(2016,12,12))
