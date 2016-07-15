import unittest
import pytest
from gosa.backend.objects.types.base import *
from gosa.backend.objects.types import ConversationNotSupported

class AnyTypeTestCase(unittest.TestCase):

    def setUp(self):
        self.type = AnyType()

    def test_is_valid_value(self):
        assert self.type.is_valid_value(False) is True
        assert self.type.is_valid_value("String") is True
        assert self.type.is_valid_value(["map"]) is True

    def test_values_match(self):
        assert self.type.values_match(False,False) is True
        assert self.type.values_match(False, True) is False

    def test_fixup(self):
        assert self.type.fixup(["1", "2"]) == [b"1",b"2"]

    def test__convert_to_integer(self):
        assert self.type._convert_to_integer(["1", "2"]) == [1, 2]

    def test__convert_from_string(self):
        assert self.type._convert_from_string(["1", "2"]) == ["1", "2"]

    def test__convert_from_datetime(self):
        assert self.type._convert_from_datetime(["1", "2"]) == ["1", "2"]

    def test__convert_to_unicodestring(self):
        assert self.type._convert_to_unicodestring(["1", "2"]) == ["1", "2"]

    def test__convert_to_boolean(self):
        assert self.type._convert_to_boolean(["1", "True","", "false", "0", "False"]) == [True, True, False, False, False, False]

class StringTypeTestCase(unittest.TestCase):

    def setUp(self):
        self.type = StringAttribute()

    def test_is_valid_value(self):
        assert self.type.is_valid_value(["String"]) is True
        assert self.type.is_valid_value([True]) is False

    def test_values_match(self):
        assert self.type.values_match(False,False) is True
        assert self.type.values_match(False, True) is False

    def test_fixup(self):
        assert self.type.fixup(["1", "2"]) == ["1","2"]

    def test__convert_to_integer(self):
        assert self.type._convert_to_integer(["1", "2"]) == [1, 2]

    def test__convert_from_string(self):
        assert self.type._convert_from_string([b"1", "2"]) == ["1", "2"]

    def test__convert_from_datetime(self):
        assert self.type._convert_from_datetime(["1", "2"]) == ["1", "2"]

    def test__convert_to_unicodestring(self):
        assert self.type._convert_to_unicodestring(["1", "2"]) == ["1", "2"]

    def test__convert_to_boolean(self):
        assert self.type._convert_to_boolean(["1", "True","", "false", "0", "False"]) == [True, True, False, False, False, False]


class IntegerTypeTestCase(unittest.TestCase):

    def setUp(self):
        self.type = IntegerAttribute()

    def test_is_valid_value(self):
        assert self.type.is_valid_value([1]) is True
        assert self.type.is_valid_value([True]) is False

    def test_values_match(self):
        assert self.type.values_match(False,False) is True
        assert self.type.values_match(False, True) is False

    def test__convert_to_integer(self):
        assert self.type._convert_to_integer([1, 2]) == [1, 2]

    def test__convert_from_integer(self):
        assert self.type._convert_from_integer([1, 2]) == [1, 2]

    def test__convert_from_string(self):
        assert self.type._convert_from_string(["1", "2", False]) == [1, 2, 0]

    def test__convert_to_string(self):
        assert self.type._convert_to_string([1, 2, 0]) == [b"1", b"2", b"0"]

    def test__convert_to_unicodestring(self):
        assert self.type._convert_to_unicodestring([1, 2]) == ["1", "2"]

    def test__convert_to_boolean(self):
        with pytest.raises(ConversationNotSupported):
            self.type._convert_to_boolean(["1"])

class BooleanTypeTestCase(unittest.TestCase):

    def setUp(self):
        self.type = BooleanAttribute()

    def test_is_valid_value(self):
        assert self.type.is_valid_value([b"String"]) is False
        assert self.type.is_valid_value([True]) is True

    def test_values_match(self):
        assert self.type.values_match(False,False) is True
        assert self.type.values_match(False, True) is False

    def test__convert_from_string(self):
        assert self.type._convert_from_string(["1", "True","", "false", "0", "False"]) == [True, True, False, False, False, False]

    def test__convert_to_unicodestring(self):
        assert self.type._convert_to_unicodestring([True, False]) == ["True", "False"]

    def test__convert_to_string(self):
        assert self.type._convert_to_string([True, False]) == [b"True", b"False"]

    def test__convert_boolean(self):
        assert self.type._convert_to_boolean([True,False]) == [True, False]
        assert self.type._convert_from_boolean([True, False]) == [True, False]

class BinaryTypeTestCase(unittest.TestCase):

    def setUp(self):
        self.type = BinaryAttribute()

    def test_convert_to_binary(self):
        assert self.type._convert_to_binary([Binary(0b1)]) == [Binary(0b1)]

    def test_convert_from_binary(self):
        assert self.type._convert_from_binary([Binary(0b1)]) == [Binary(0b1)]

    def test_is_valid_value(self):
        assert self.type.is_valid_value([Binary(0b1)]) is True
        assert self.type.is_valid_value([88]) is False

    def test_values_match(self):
        assert self.type.values_match(Binary(0b1),Binary(0b1)) is True
        assert self.type.values_match(Binary(0b1), Binary(0b10)) is False

    def test__convert_to_string(self):
        assert self.type._convert_to_string([Binary(0b1), Binary(0b10)]) == [b"1",b"2"]

    def test__convert_to_unicodestring(self):
        assert self.type._convert_to_unicodestring([Binary(0b1), Binary(0b10)]) == ["1", "2"]

#
class UnicodeStringTypeTestCase(unittest.TestCase):

    def setUp(self):
        self.type = UnicodeStringAttribute()

    def test_is_valid_value(self):
        assert self.type.is_valid_value(["String"]) is True
        assert self.type.is_valid_value([b"String"]) is False

    def test_values_match(self):
        assert self.type.values_match("Test","Test") is True
        assert self.type.values_match("Test", "test") is False

    def test__convert_from_string(self):
        assert self.type._convert_from_string(["1", "2", False]) == ["1", "2", ""]

    def test__convert_from_unicodestring(self):
        assert self.type._convert_from_unicodestring(["1", "2"]) == ["1", "2"]

    def test__convert_to_unicodestring(self):
        assert self.type._convert_to_unicodestring(["1", "2"]) == ["1", "2"]

    def test__convert_to_string(self):
        assert self.type._convert_to_string([b"1", b"2"]) == ["1", "2"]

class DateTypeTestCase(unittest.TestCase):

    def setUp(self):
        self.type = DateAttribute()

    def test_convert_to_date(self):
        date = datetime.date.today()
        assert self.type._convert_to_date([date]) == [date]

    def test_convert_from_date(self):
        date = datetime.date.today()
        assert self.type._convert_from_date([date]) == [date]

    def test_is_valid_value(self):
        assert self.type.is_valid_value([datetime.date.today()]) is True
        assert self.type.is_valid_value([True]) is False

    def test_values_match(self):
        assert self.type.values_match(datetime.date.today(),datetime.date.today()) is True
        assert self.type.values_match(datetime.date.today(), datetime.date(2016, 1, 1)) is False

    def test__convert_to_string(self):
        assert self.type._convert_to_string([datetime.date(2016, 1, 1)]) == [b"2016-01-01"]

    def test__convert_to_unicodestring(self):
        assert self.type._convert_to_unicodestring([datetime.date(2016, 1, 1)]) == ["2016-01-01"]

#
class TimestampTypeTestCase(unittest.TestCase):

    def setUp(self):
        self.type = TimestampAttribute()

    def test_convert_to_timestamp(self):
        date = datetime.datetime.now()
        assert self.type._convert_to_timestamp([date]) == [date]

    def test_convert_from_timestamp(self):
        date = datetime.datetime.now()
        assert self.type._convert_from_timestamp([date]) == [date]

    def test_is_valid_value(self):
        assert self.type.is_valid_value([datetime.datetime.now()]) is True
        assert self.type.is_valid_value([True]) is False

    def test_values_match(self):
        date = datetime.datetime.now()
        assert self.type.values_match(date, date) is True
        assert self.type.values_match(date, datetime.datetime(2016, 1, 1, 0, 0, 0)) is False

    def test__convert_to_string(self):
        assert self.type._convert_to_string([datetime.datetime(2016, 1, 1, 0, 0, 0)]) == [b"2016-01-01T00:00:00"]

    def test__convert_to_unicodestring(self):
        assert self.type._convert_to_unicodestring([datetime.datetime(2016, 1, 1, 0, 0, 0)]) == ["2016-01-01T00:00:00"]
