#!/usr/bin/python3

import unittest
import datetime
import calendar
from gosa.common.components.scheduler.triggers.cron.fields import *
from gosa.common.components.scheduler.triggers.cron.expressions import *

class FieldsTestCase(unittest.TestCase):
    def test_baseField(self):
        bf = BaseField("month", "2", is_default=False)
        assert bf.is_default == False
        
        bf = BaseField("month", "4,8,12", is_default=True)
        assert bf.is_default == True
        assert bf.get_min(None) == 1
        assert bf.get_max(None) == 12
        # Note: get_min and get_max do not use the dateval parameter.
        
        assert bf.get_value(datetime.datetime(2016, 12, 13)) == 12
        
        assert bf.get_next_value(datetime.datetime(2016, 12, 13)) == 12
        assert bf.get_next_value(datetime.datetime(2016, 1, 13)) == 4
        
        assert str(bf) == "4,8,12"
        assert repr(bf) == "BaseField('month', '%s')" % str(bf)
        
        self.assertRaises(ValueError, BaseField, "month", "testing")
    
    def test_weekField(self):
        assert WeekField.REAL == False
        
        wf = WeekField("week", "1,2")
        dt = datetime.datetime(2016,12,12)
        assert wf.get_value(dt) == dt.isocalendar()[1] == 50
    
    def test_dayOfMonthField(self):
        assert DayOfMonthField.COMPILERS == BaseField.COMPILERS + [WeekdayPositionExpression, LastDayOfMonthExpression]
        
        domf = DayOfMonthField("day", "12,14")
        dt = datetime.datetime(2016,12,12)
        assert domf.get_max(dt) == calendar.monthrange(dt.year, dt.month)[1] == 31
    
    def test_DayOfWeekField(self):
        assert DayOfWeekField.REAL == False
        assert DayOfWeekField.COMPILERS == BaseField.COMPILERS + [WeekdayRangeExpression]
        
        domf = DayOfWeekField("day_of_week", "1,2")
        dt = datetime.datetime(2016,12,12)
        assert domf.get_value(dt) == dt.weekday() == 0
