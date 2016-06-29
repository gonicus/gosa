# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from gosa.backend.objects.types import AttributeType
from gosa.common.components.jsonrpc_utils import Binary
import datetime


class AnyType(AttributeType):
    __alias__ = "AnyType"

    def is_valid_value(self, value):
        return True

    def values_match(self, value1, value2):
        return value1 == value2

    def _convert_from_string(self, value):
        return value

    def _convert_from_datetime(self, value):
        return value

    def _convert_to_boolean(self, value):
        return list(map(lambda x: not(x in ['', 'false', '0', 'False']), value))

    def _convert_to_string(self, value):
        return list(map(lambda x: bytes(x, 'utf-8'), value))

    def _convert_to_integer(self, value):
        return list(map(lambda x: int(x), value))

    def _convert_to_unicodestring(self, value):
        return list(map(lambda x: str(x), value))

    def fixup(self, value):
        return self._convert_to_string(value)


class StringAttribute(AttributeType):
    __alias__ = "String"

    def _convert_from_string(self, value):
        new_value = []
        for item in value:
            if not item and type(item) != bytes:
                item = ""
            new_value.append(item)
        return new_value

    def is_valid_value(self, value):
        return not len(value) or all(map(lambda x: type(x) == bytes, value))

    def values_match(self, value1, value2):
        return value1 == value2

    def _convert_to_boolean(self, value):
        return list(map(lambda x: not(x in ['', 'false', '0', 'False']), value))

    def _convert_to_string(self, value):
        return list(map(lambda x: bytes(x, 'utf-8'), value))

    def _convert_to_integer(self, value):
        return list(map(lambda x: int(x), value))

    def _convert_to_unicodestring(self, value):
        return list(map(lambda x: str(x), value))

    def _convert_from_datetime(self, value):
        return list(map(lambda x: bytes(str(x), 'utf-8'), value))

    def fixup(self, value):
        return self._convert_to_string(value)


class IntegerAttribute(AttributeType):
    __alias__ = "Integer"

    def _convert_to_integer(self, value):
        return value

    def _convert_from_integer(self, value):
        return value

    def is_valid_value(self, value):
        return not len(value) or all(map(lambda x: type(x) == int, value))

    def values_match(self, value1, value2):
        return value1 == value2

    def _convert_to_string(self, value):
        return list(map(lambda x: bytes(str(x), 'utf-8'), value))

    def _convert_to_unicodestring(self, value):
        return list(map(lambda x: str(x), value))

    def _convert_from_string(self, value):
        return list(map(lambda x: int(x), value))


class BooleanAttribute(AttributeType):
    __alias__ = "Boolean"

    def is_valid_value(self, value):
        return not len(value) or all(map(lambda x: type(x) == bool, value))

    def _convert_to_boolean(self, value):
        return value

    def _convert_from_boolean(self, value):
        return value

    def values_match(self, value1, value2):
        return value1 == value2

    def _convert_to_string(self, value):
        return list(map(lambda x: bytes(str(x), 'utf-8'), value))

    def _convert_to_unicodestring(self, value):
        return list(map(lambda x: str(x), value))

    def _convert_from_string(self, value):
        return list(map(lambda x: not(x in ['', 'false', '0', 'False']), value))


class BinaryAttribute(AttributeType):
    __alias__ = "Binary"

    def _convert_to_binary(self, value):
        return value

    def _convert_from_binary(self, value):
        return value

    def is_valid_value(self, value):
        return not len(value) or all(map(lambda x: type(x) == Binary, value))

    def values_match(self, value1, value2):
        return value1 == value2

    def _convert_to_string(self, value):
        return list(map(lambda x: bytes(str(x.get()), 'utf-8'), value))

    def _convert_to_unicodestring(self, value):
        return list(map(lambda x: str(x.get()), value))


class UnicodeStringAttribute(AttributeType):
    __alias__ = "UnicodeString"

    def _convert_from_unicodestring(self, value):
        #TODO: is this enough?
        return value

    def is_valid_value(self, value):
        return not len(value) or all(map(lambda x: type(x) == str, value))

    def values_match(self, value1, value2):
        return value1 == value2

    def _convert_to_string(self, value):
        return list(map(lambda x: bytes(x, 'utf-8'), value))

    def _convert_to_unicodestring(self, value):
        return list(map(lambda x: str(x), value))

    def _convert_from_string(self, value):
        new_value = []
        for item in value:
            if not item and type(item) not in [bytes, str]:
                item = u""
            new_value.append(str(item))
        return new_value


class DateAttribute(AttributeType):
    __alias__ = "Date"

    def _convert_to_date(self, value):
        return value

    def _convert_from_date(self, value):
        return value

    def is_valid_value(self, value):
        return not len(value) or all(map(lambda x: type(x) == datetime.date, value))

    def values_match(self, value1, value2):
        return value1 == value2

    def _convert_to_string(self, value):
        return list(map(lambda x: bytes(x.strftime("%Y-%m-%d"), 'utf-8'), value))

    def _convert_to_unicodestring(self, value):
        return list(map(lambda x: str(x.strftime("%Y-%m-%d")), value))


class TimestampAttribute(AttributeType):
    __alias__ = "Timestamp"

    def _convert_to_timestamp(self, value):
        return value

    def _convert_from_timestamp(self, value):
        return value

    def is_valid_value(self, value):
        return not len(value) or all(map(lambda x: type(x) == datetime.datetime, value))

    def values_match(self, value1, value2):
        return value1 == value2

    def _convert_to_string(self, value):
        return list(map(lambda x: bytes(x.strftime("%Y-%m-%dT%H:%M:%S%z"),'utf-8'), value))

    def _convert_to_unicodestring(self, value):
        return list(map(lambda x: str(x.strftime("%Y-%m-%dT%H:%M:%S%z")), value))
