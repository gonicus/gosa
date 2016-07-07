#!/usr/bin/python3

import unittest
import datetime
from gosa.common.components.scheduler.triggers.simple import *

#def convert_to_datetime_mock(*args, **kwargs):
    #return datetime.datetime(2016, 7, 1, 10, 16, 36)

class SimpleTriggerTestCase(unittest.TestCase):
    #@unittest.mock.patch("gosa.common.components.scheduler.triggers.simple.convert_to_datetime", convert_to_datetime_mock)
    def test_simpleTrigger(self):
        t = SimpleTrigger("2016-12-12")
        assert t.get_next_fire_time(datetime.datetime(2016,12,11)) == datetime.datetime(2016,12,12)
        assert str(t) == "date[%s]" % str(datetime.datetime(2016,12,12))
        assert repr(t) == "<SimpleTrigger (run_date=%s)>" % repr(datetime.datetime(2016,12,12))
