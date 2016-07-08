#!/usr/bin/python3

import unittest
import pytest
from gosa.common.components.scheduler.triggers.cron import *

class CronTriggerTestCase(unittest.TestCase):
    def test_cronTrigger(self):
        with pytest.raises(TypeError):
            CronTrigger(invalid="*")
        t = CronTrigger(start_date="2016-12-12", year="*", hour="12", minute=None)
        
        assert str(t) == "cron[year='*', hour='12']"
        assert repr(t) == "<CronTrigger (year='*', hour='12', start_date='2016-12-12 00:00:00')>"
        
        t = CronTrigger()
        
        assert str(t) == "cron[]"
        assert repr(t) == "<CronTrigger ()>"
        
        assert CronTrigger.FIELD_NAMES == ('year', 'month', 'day', 'week', 'day_of_week', 'hour', 'minute', 'second')
    def test__increment_field_value(self):
        t = CronTrigger(hour="12")
        dt = datetime(2016, 6, 12)
        # Second parameter numbers are indexes of CronTrigger.FIELD_NAMES
        assert t._increment_field_value(dt, 2) == (datetime(2016, 6, 13), 2)
        assert t._increment_field_value(dt, 4) == (datetime(2016, 6, 13), 2)
        assert t._increment_field_value(dt, 5) == (datetime(2016, 6, 12, 1), 5)
        dt = datetime(2016, 6, 30)
        assert t._increment_field_value(dt, 2) == (datetime(2016, 7, 1), 1)
    def test__set_field_value(self):
        t = CronTrigger(hour="12")
        dt = datetime(2016, 6, 12)
        assert t._set_field_value(dt, 2, 8) == datetime(2016, 6, 8)
        # Note: _set_field_value won't change not REAL fields.
    def test_get_next_fire_time(self):
        t = CronTrigger(hour="12")
        dt = datetime(2016, 6, 12)
        assert t.get_next_fire_time(dt) == datetime(2016, 6, 12, 12, 0, 0)
        
        t = CronTrigger(start_date="2016-06-12 12:29:55", second="12")
        assert t.get_next_fire_time(dt) == datetime(2016, 6, 12, 12, 30, 12)
        
        t = CronTrigger(start_date="2016-06-12 12:29:55", day_of_week="3")
        assert t.get_next_fire_time(dt) == datetime(2016, 6, 16, 0, 0)
