#!/usr/bin/python3

import unittest
import datetime
from gosa.common.components.scheduler.util import *

class TestDummy:
    def __call__(self, value):
        super(TestDummy, self).__call__(value)
    @staticmethod
    def static_dummy():
        pass
    @classmethod
    def class_dummy():
        pass

class UtilTestCase(unittest.TestCase):
    def test_asint(self):
        self.assertEqual(asint("123"), 123)
        self.assertEqual(asint(None), None)
    def test_asbool(self):
        self.assertTrue(asbool({"Any": "object unlike string"}))
        self.assertFalse(asbool(0))
        
        self.assertRaises(ValueError, asbool, "any string")
        self.assertRaises(ValueError, asbool, "")
        
        for yes in ('true', 'yes', 'on', 'y', 't', '1'):
            self.assertTrue(asbool(yes))
        for no in ('false', 'no', 'off', 'n', 'f', '0'):
            self.assertFalse(asbool(no))
    def test_convert_to_datetime(self):
        d = datetime.datetime.now()
        self.assertEqual(convert_to_datetime(d), d)
        
        d = datetime.date.today()
        self.assertEqual(d, convert_to_datetime(d).date())
        
        d = """2016-06-24"""
        self.assertEqual(convert_to_datetime(d), datetime.datetime(2016, 6, 24))
        
        d = """2016-06-24 15:40:32"""
        self.assertEqual(convert_to_datetime(d), datetime.datetime(2016, 6, 24, 15, 40, 32))
        
        d = """2016-06-24 15:40:32.456"""
        self.assertEqual(convert_to_datetime(d), datetime.datetime(2016, 6, 24, 15, 40, 32, 456))
        
        self.assertRaises(TypeError, convert_to_datetime, {"a": "dict"})
        self.assertRaises(ValueError, convert_to_datetime, "malformed string")
    def test_timedelta_seconds(self):
        # Alternative: timedelta.total_seconds (new in Python 3.2)
        d = datetime.timedelta(days=1, seconds=31)
        self.assertEqual(timedelta_seconds(d), 24*60*60+31)
    def test_time_difference(self):
        d1 = datetime.datetime(2016,6,24,12)
        d2 = datetime.datetime(2016,6,24,11)
        self.assertEqual(time_difference(d1, d2), 60*60)
    def test_datetime_ceil(self):
        d1 = datetime.datetime(2016,6,24,12,12,51,789)
        d2 = datetime.datetime(2016,6,24,12,12,52)
        self.assertEqual(datetime_ceil(d1), d2)
        self.assertEqual(datetime_ceil(d2), d2)
    def test_combine_opts(self):
        global_config = {"pref_test1": {"subdict": "TEST"},
            "pref_test2": "will be overwritten",
            "test3": "wants to be removed",
            "pref_test4": "wants to stay"
        }
        local_config = {"test2": "Replace global"}
        self.assertEqual(combine_opts(global_config, "pref_", local_config),
            {'test4': 'wants to stay', 'test2': 'Replace global', 'test1': {'subdict': 'TEST'}})
    def test_get_callable_name(self):
        def dummy():
            pass
        dummy_obj = TestDummy()
        self.assertEqual(get_callable_name(dummy), "dummy")
        self.assertEqual(get_callable_name(self.assertEqual), "UtilTestCase.assertEqual")
        self.assertEqual(get_callable_name(dummy_obj.static_dummy), "static_dummy")
        self.assertEqual(get_callable_name(TestDummy.static_dummy), "static_dummy")
        self.assertEqual(get_callable_name(TestDummy.class_dummy), "TestDummy.class_dummy")
        self.assertEqual(get_callable_name(dummy_obj), "TestDummy")
        
        self.assertRaises(TypeError, get_callable_name, "")
    def test_obj_to_ref(self):
        self.assertEqual(obj_to_ref(datetime.timedelta), "datetime:timedelta")
        
        dummy_obj = TestDummy()
        self.assertRaises(ValueError, obj_to_ref, dummy_obj)
    def test_ref_to_obj(self):
        self.assertEqual(ref_to_obj("datetime:timedelta"), datetime.timedelta)
        
        self.assertRaises(TypeError, ref_to_obj, {"a": "dict"})
        self.assertRaises(ValueError, ref_to_obj, "not_existant_module_name") # Without ":"
        
        try:
            __import__("not_existant_module_name")
        except ImportError: # Maybe "not_existant_module_name" exists...
            self.assertRaises(LookupError, ref_to_obj, "not_existant_module_name:not_existant_module_name")
        
        self.assertRaises(LookupError, ref_to_obj, "datetime:not_existant_module_name")
        
        #from gosa.common.components.registry import PluginRegistry
        # Won't work...
        #self.assertEqual(ref_to_obj("gosa.agent.command:CommandRegistry.dispatch"),
            #getattr(PluginRegistry.getInstance('CommandRegistry'), "dispatch") )
    def test_maybe_ref(self):
        self.assertEqual(maybe_ref("datetime:timedelta"), datetime.timedelta)
        self.assertEqual(maybe_ref(datetime.timedelta), datetime.timedelta)
    def test_to_unicode(self):
        self.assertEqual(to_unicode("a string"), "a string")
        self.assertEqual(to_unicode("a string ü".encode()), "a string ") # Omits unicode chars...
        self.assertEqual(to_unicode("a string ü".encode(), encoding="utf-8"), "a string ü")
        self.assertEqual(to_unicode("a string".encode("ascii")), "a string")
