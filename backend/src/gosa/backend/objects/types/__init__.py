# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import inspect
from gosa.common.utils import N_
from gosa.common.error import GosaErrorHandler as C
from gosa.backend.exceptions import ConversationNotSupported
__import__('pkg_resources').declare_namespace(__name__)


# Register the errors handled  by us
C.register_codes(dict(
    TYPE_NO_CHECK=N_("Cannot check value of type %(type)s"),
    TYPE_NO_MATCH=N_("Cannot match value of type %(type)s"),
    TYPE_NO_CONVERT=N_("Cannot convert from '%(source)s' type to '%(target)s' type"),
    ))


class AttributeType(object):

    __alias__ = ""

    def _cnv_topic(self):
        fname = inspect.stack()[1][3]
        if fname[:12:] == "_convert_to_":
            return self.__alias__.lower(), fname[12:].replace("_", " ")
        else:
            return self.__alias__.lower(), fname[14:].replace("_", " ")

    def is_valid_value(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CHECK', type=self.__alias__.lower()))

    def values_match(self, value1, value2):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_MATCH', type=self.__alias__.lower()))

    def convert_to(self, target_type, value):
        cnv = getattr(self, "_convert_to_%s" % target_type.lower())
        return cnv(value)

    def fixup(self, value):  # pragma: nocover
        return value

    def convert_from(self, source_type, value):
        cnv = getattr(self, "_convert_from_%s" % source_type.lower())
        return cnv(value)

    def _convert_to_boolean(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CONVERT',
                                                    source=self.__alias__.lower(),
                                                    target=self._cnv_topic()[1]))

    def _convert_to_string(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CONVERT',
                                                    source=self.__alias__.lower(),
                                                    target=self._cnv_topic()[1]))

    def _convert_to_unicodestring(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CONVERT',
                                                    source=self.__alias__.lower(),
                                                    target=self._cnv_topic()[1]))

    def _convert_to_integer(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CONVERT',
                                                    source=self.__alias__.lower(),
                                                    target=self._cnv_topic()[1]))

    def _convert_to_timestamp(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CONVERT',
                                                    source=self.__alias__.lower(),
                                                    target=self._cnv_topic()[1]))

    def _convert_to_date(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CONVERT',
                                                    source=self.__alias__.lower(),
                                                    target=self._cnv_topic()[1]))

    def _convert_to_binary(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CONVERT',
                                                    source=self.__alias__.lower(),
                                                    target=self._cnv_topic()[1]))

    def _convert_from_boolean(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CONVERT',
                                                    target=self.__alias__.lower(),
                                                    source=self._cnv_topic()[1]))

    def _convert_from_string(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CONVERT',
                                                    target=self.__alias__.lower(),
                                                    source=self._cnv_topic()[1]))

    def _convert_from_unicodestring(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CONVERT',
                                                    target=self.__alias__.lower(),
                                                    source=self._cnv_topic()[1]))

    def _convert_from_integer(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CONVERT',
                                                    target=self.__alias__.lower(),
                                                    source=self._cnv_topic()[1]))

    def _convert_from_timestamp(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CONVERT',
                                                    target=self.__alias__.lower(),
                                                    source=self._cnv_topic()[1]))

    def _convert_from_date(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CONVERT',
                                                    target=self.__alias__.lower(),
                                                    source=self._cnv_topic()[1]))

    def _convert_from_binary(self, value):  # pragma: nocover
        raise ConversationNotSupported(C.make_error('TYPE_NO_CONVERT',
                                                    target=self.__alias__.lower(),
                                                    source=self._cnv_topic()[1]))
