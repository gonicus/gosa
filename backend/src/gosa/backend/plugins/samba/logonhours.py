# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import time
from gosa.backend.objects.types import AttributeType


class SambaLogonHoursAttribute(AttributeType):
    """
    This is a special object-attribute-type for sambaLogonHours.

    This call can convert sambaLogonHours to a UnicodeString and vice versa.
    It is used in the samba-object definition file.
    """

    __alias__ = "SambaLogonHours"

    def values_match(self, value1, value2):
        return str(value1) == str(value2)

    def is_valid_value(self, value):
        if len(value):
            try:

                # Check if each week day contains 24 values.
                if type(value[0]) not in  [str, unicode] or len(value[0]) != 168 or len(set(value[0]) - set('01')):
                    return False
                return True

            except:
                return False

    def _convert_to_unicodestring(self, value):
        """
        This method is a converter used when values gets read from or written to the backend.

        Converts the 'SambaLogonHours' object-type into a 'UnicodeString'-object.
        """
        if len(value):

            # Combine the binary strings
            lstr = value[0]

            # New reverse every 8 bit part, and toggle high- and low-tuple (4Bits)
            new = ""
            for i in range(0, 21):
                n = lstr[i * 8:((i + 1) * 8)]
                n = n[0:4] + n[4:]
                n = n[::-1]
                n = str(hex(int(n, 2)))[2::].rjust(2, '0')
                new += n
            value = [new.upper()]

        return value

    def _convert_from_string(self, value):
        return self._convert_from_unicodestring(value)

    def _convert_from_unicodestring(self, value):
        """
        This method is a converter used when values gets read from or written to the backend.

        Converts a 'UnicodeString' attribute into the 'SambaLogonHours' object-type.
        """

        if len(value):

            # Convert each hex-pair into binary values.
            # Then reverse the binary result and switch high and low pairs.
            value = value[0]
            lstr = ""
            for i in range(0, 42, 2):
                n = (bin(int(value[i:i + 2], 16))[2::]).rjust(8, '0')
                n = n[::-1]
                lstr += n[0:4] + n[4:]

            # Shift lster by timezone offset
            shift_by = (168 + (time.timezone/3600)) % 168
            lstr = lstr[shift_by:] + lstr[:shift_by]

            # Parse result into more readable value
            value = [lstr]

        return value
