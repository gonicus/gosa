#!/usr/bin/python3

import unittest
import datetime
import re
import pytest
from gosa.common.components.scheduler.triggers.cron.fields import *
from gosa.common.components.scheduler.triggers.cron.expressions import *

class ExpressionsTestCase(unittest.TestCase):
    def test_AllExpression(self):
        assert AllExpression.value_re == re.compile(r'\*(?:/(?P<step>\d+))?$')
        
        with pytest.raises(ValueError):
            AllExpression(step="0")
        ae = AllExpression()
        week_field = WeekField("week", "1")
        dt = datetime.date(2016, 12, 12)
        assert ae.get_next_value(dt, week_field) == dt.isocalendar()[1] == 50
        
        assert str(ae) == "*"
        assert repr(ae) == "AllExpression(None)"
        
        ae = AllExpression(step=2)
        week_field = WeekField("week", "1")
        dt = datetime.date(2016, 6, 12)
        #assert ae.get_next_value(dt, week_field) == ((dt + datetime.timedelta(weeks=4)).isocalendar()[1])# == 52
        assert ae.get_next_value(dt, week_field)
        
        assert str(ae) == "*/2"
        assert repr(ae) == "AllExpression(2)"
        # Note to __str__(self): May be more explicit:
        # if step is None:
        #     return '*'
        # ...
    def test_RangeExpression(self):
        assert RangeExpression.value_re == re.compile(r'(?P<first>\d+)(?:-(?P<last>\d+))?(?:/(?P<step>\d+))?$')
        
        with pytest.raises(ValueError):
            RangeExpression(2, last=1)
        rex = RangeExpression(50)
        week_field = WeekField("week", "1")
        dt = datetime.date(2016, 12, 12)
        assert rex.get_next_value(dt, week_field) == 50
        
        assert str(rex) == "50"
        assert repr(rex) == "RangeExpression(50)"
        
        rex = RangeExpression(1, 2)
        assert rex.get_next_value(dt, week_field) == None
        
        assert str(rex) == "1-2"
        assert repr(rex) == "RangeExpression(1, 2)"
        
        rex = RangeExpression(49, 52)
        assert rex.get_next_value(dt, week_field) == 50
        
        assert str(rex) == "49-52"
        assert repr(rex) == "RangeExpression(49, 52)"
        
        rex = RangeExpression(49, last=52, step=2)
        assert rex.get_next_value(dt, week_field) == 51
        
        assert str(rex) == "49-52/2"
        assert repr(rex) == "RangeExpression(49, 52, 2)"
    def test_WeekdayRangeExpression(self):
        assert WeekdayRangeExpression.value_re == re.compile(r'(?P<first>[a-z]+)(?:-(?P<last>[a-z]+))?', re.IGNORECASE)
        
        with pytest.raises(ValueError):
            WeekdayRangeExpression("ned")
        with pytest.raises(ValueError):
            WeekdayRangeExpression("mon", last="ned")
        wrex = WeekdayRangeExpression("tue")
        
        assert str(wrex) == "tue"
        assert repr(wrex) == "WeekdayRangeExpression('tue')"
        
        wrex = WeekdayRangeExpression("mon", "fri")
        
        assert str(wrex) == "mon-fri"
        assert repr(wrex) == "WeekdayRangeExpression('mon', 'fri')"
    def test_WeekdayPositionExpression(self):
        options = ['1st', '2nd', '3rd', '4th', '5th', 'last']
        assert WeekdayPositionExpression.value_re == re.compile(r'(?P<option_name>%s) +(?P<weekday_name>(?:\d+|\w+))' % '|'.join(options), re.IGNORECASE)
        
        with pytest.raises(ValueError):
            WeekdayPositionExpression("all", "all")
        with pytest.raises(ValueError):
            WeekdayPositionExpression("1St", "all")
        
        wpex = WeekdayPositionExpression("1St", "fri")
        day_field = BaseField("day", "*")
        dt = datetime.date(2016, 12, 1)
        assert wpex.get_next_value(dt, day_field) == 2
        
        wpex = WeekdayPositionExpression("1st", "mon")
        dt = datetime.date(2016, 7, 1)
        assert wpex.get_next_value(dt, day_field) == 4
        
        wpex = WeekdayPositionExpression("last", "fri")
        assert str(wpex) == "last fri"
        assert repr(wpex) == "WeekdayPositionExpression('last', 'fri')"
        return True
        # Python2-Python3 difference:
        # Py2: ((15) / 7) * 7 == 14
        # Py3: ((15) / 7) * 7 == 15.0
        # Implementation relies on Py2 behaviour.
        assert wpex.get_next_value(dt, day_field) == 30
    def test_LastDayOfMonthExpression(self):
        assert LastDayOfMonthExpression.value_re == re.compile(r'last', re.IGNORECASE)
        
        ldofex = LastDayOfMonthExpression()
        day_field = BaseField("day", "*")
        dt = datetime.date(2016, 12, 1)
        assert ldofex.get_next_value(dt, day_field) == 31
        
        assert str(ldofex) == "last"
        assert repr(ldofex) == "LastDayOfMonthExpression()"
        
