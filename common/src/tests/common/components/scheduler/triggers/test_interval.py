#!/usr/bin/python3

import unittest
import pytest
from gosa.common.components.scheduler.triggers.interval import *

class IntervalTriggerTestCase(unittest.TestCase):
    #@unittest.mock.patch("gosa.common.components.scheduler.triggers.simple.convert_to_datetime", convert_to_datetime_mock)
    def test_intervalTrigger(self):
        with pytest.raises(TypeError):
            IntervalTrigger("TEST")
        
        with unittest.mock.patch.object(datetime, "datetime", unittest.mock.Mock(wraps=datetime.datetime)) as datetimeMock:
            now_dt = datetime.datetime(2016, 12, 12)
            datetimeMock.now.return_value = now_dt
            # Automatic set time to 1s
            t = IntervalTrigger(datetime.timedelta())
            assert t.start_date == now_dt + datetime.timedelta(seconds=1)
            assert t.interval == datetime.timedelta(seconds=1)
            assert t.interval_length == 1
        
        t = IntervalTrigger(datetime.timedelta(days=2), start_date="2016-12-12")
        assert t.get_next_fire_time(datetime.datetime(2016, 12, 11)) == datetime.datetime(2016, 12, 12)
        
        assert t.get_next_fire_time(datetime.datetime(2016, 12, 14)) == datetime.datetime(2016, 12, 14)
        assert t.get_next_fire_time(datetime.datetime(2016, 12, 15)) == datetime.datetime(2016, 12, 16)
        
        assert t.get_next_fire_time(datetime.datetime(2016, 12, 16)) == datetime.datetime(2016, 12, 16)
        assert t.get_next_fire_time(datetime.datetime(2016, 12, 17)) == datetime.datetime(2016, 12, 18)
        
        assert str(t) == "interval[%s]" % str(datetime.timedelta(days=2))
        assert repr(t) == "<IntervalTrigger (interval=%s, start_date=%s)>" % (repr(datetime.timedelta(days=2)), repr(datetime.datetime(2016,12,12)))
