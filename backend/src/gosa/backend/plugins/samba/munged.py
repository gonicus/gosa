# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from base64 import b64decode, b64encode
from binascii import hexlify, unhexlify
from gosa.backend.objects.filter import ElementFilter
from gosa.common.error import ClacksErrorHandler as C


class SambaMungedDialOut(ElementFilter):
    """
    Out-Filter for sambaMungedDial.
    """

    def __init__(self, obj):
        super(SambaMungedDialOut, self).__init__(obj)

    def process(self, obj, key, valDict):

        # Create a dictionary with all relevant samba attributes.
        alist = ['CtxCallback', 'CtxCallbackNumber', 'CtxCfgFlags1', 'CtxCfgPresent',
                 'CtxInitialProgram', 'CtxKeyboardLayout', 'CtxMaxConnectionTime',
                 'CtxMaxDisconnectionTime', 'CtxMaxIdleTime', 'Ctx_flag_connectClientDrives',
                 'CtxMinEncryptionLevel', 'oldStorageBehavior',
                 'CtxNWLogonServer', 'CtxShadow', 'CtxWFHomeDir', 'CtxWFHomeDirDrive',
                 'CtxWFProfilePath', 'CtxWorkDirectory', 'Ctx_flag_brokenConn',
                 'Ctx_flag_connectClientPrinters', 'Ctx_flag_defaultPrinter',
                 'Ctx_flag_inheritMode', 'Ctx_flag_reConn', 'Ctx_shadow', 'Ctx_flag_tsLogin']

        # Build up a list of values to encode.
        res = {}
        for entry in alist:
            if not len(valDict[entry]['value']):
                raise AttributeError(C.make_error('ATTRIBUTE_MANDATORY', entry))
            else:
                res[entry] = valDict[entry]['value'][0]

        # Encode the sambaMungedDial attribute.
        result = SambaMungedDial.encode(res)
        valDict[key]['value'] = [result]

        return key, valDict


class SambaMungedDialIn(ElementFilter):
    """
    In-Filter for sambaMungedDial.
    """

    def __init__(self, obj):
        super(SambaMungedDialIn, self).__init__(obj)

    def process(self, obj, key, valDict):

        if len(valDict[key]['value']):

            # Create a dictionary with all relevant samba attributes.
            alist = {
                    'oldStorageBehavior': 'Boolean',
                    'CtxCallback': 'UnicodeString',
                    'CtxCallbackNumber': 'UnicodeString',
                    'CtxCfgFlags1': 'UnicodeString',
                    'CtxCfgPresent': 'UnicodeString',
                    'CtxInitialProgram': 'UnicodeString',
                    'CtxKeyboardLayout': 'UnicodeString',
                    'CtxMaxConnectionTime': 'Integer',
                    'CtxMaxDisconnectionTime': 'Integer',
                    'CtxMaxIdleTime': 'Integer',
                    'CtxMinEncryptionLevel': 'Integer',
                    'CtxNWLogonServer': 'UnicodeString',
                    'CtxShadow': 'UnicodeString',
                    'CtxWFHomeDir': 'UnicodeString',
                    'CtxWFHomeDirDrive': 'UnicodeString',
                    'CtxWFProfilePath': 'UnicodeString',
                    'CtxWorkDirectory': 'UnicodeString',
                    'Ctx_flag_brokenConn': 'Boolean',
                    'Ctx_flag_connectClientDrives': 'Boolean',
                    'Ctx_flag_connectClientPrinters': 'Boolean',
                    'Ctx_flag_defaultPrinter': 'Boolean',
                    'Ctx_flag_inheritMode': 'Boolean',
                    'Ctx_flag_reConn': 'Boolean',
                    'Ctx_shadow': 'Integer',
                    'Ctx_flag_tsLogin': 'Boolean'}

            # Update the value of the read property
            md = valDict[key]['value'][0]
            res = SambaMungedDial.decode(md)

            for entry in alist:
                if entry in res:
                    valDict[entry]['value'] = [res[entry]]
                    valDict[entry]['skip_save'] = True

        return key, valDict


class SambaMungedDial(object):
    """
    This class allows to convert the sambaMungedDial attribute into
    a human readable list of properties and vice versa.

    (All methods are declared static, due to the fact that this
    methods gets called from within in- and out-filters!)
    """

    # A list of all string values included in the samba
    # mungedDial
    stringParams = ["CtxWorkDirectory",
            "CtxNWLogonServer",
            "CtxWFHomeDir",
            "CtxWFHomeDirDrive",
            "CtxWFProfilePath",
            "CtxInitialProgram",
            "CtxCallbackNumber"]

    # A list of time values
    timeParams = ["CtxMaxConnectionTime",
            "CtxMaxDisconnectionTime",
            "CtxMaxIdleTime"]

    # The old sambaMungedDial header.
    new_header = "20002000200020002000200020002000" \
            "20002000200020002000200020002000"  \
            "20002000200020002000200020002000"  \
            "20002000200020002000200020002000"  \
            "20002000200020002000200020002000"  \
            "20002000200020002000200020002000"  \
            "5000"

    # The old sambaMungedDial header.
    old_header = "6d000800200020002000200020002000" \
            "20002000200020002000200020002000"  \
            "20002000200020002000200064000100"  \
            "20002000200020002000200020002000"  \
            "20002000200020002000200020002000"  \
            "20002000200020002000200020002000"  \
            "50001000"

    @staticmethod
    def encode(values):
        """
        Encodes the given value dictionary into a sambaMungedDial attribute.

        =========== ===============================
        Key         Description
        =========== ===============================
        values      A dictionary containing all munged dial relevant values.
        =========== ===============================
        """

        # Build up 'CtxCfgFlags1' property.
        flags = list(values['CtxCfgFlags1'])

        # Handle flag at position 2
        flag = int(flags[2], 16)
        if values['Ctx_flag_defaultPrinter']:
            flag |= 2
        else:
            flag &= 0xFF & ~0x2

        if values['Ctx_flag_connectClientDrives']:
            flag |= 8
        else:
            flag &= 0xFF & ~0x8

        if values['Ctx_flag_connectClientPrinters']:
            flag |= 4
        else:
            flag &= 0xFF & ~0x4
        flags[2] = hex(flag)[2:]

        # Handle flag at position 5
        flag = int(flags[5], 16)
        if values['Ctx_flag_tsLogin']:
            flag |= 1
        else:
            flag &= 0xFF & ~0x1

        if values['Ctx_flag_reConn']:
            flag |= 2
        else:
            flag &= 0xFF & ~0x2

        if values['Ctx_flag_brokenConn']:
            flag |= 4
        else:
            flag &= 0xFF & ~0x4

        flags[5] = hex(flag)[2:]
        flags[6] = '1' if values['Ctx_flag_inheritMode'] else '0'

        # Add shadow handling.
        if values['oldStorageBehavior']:
            flags[1] = '%1X' % values['Ctx_shadow']
        values['CtxCfgFlags1'] = ''.join(flags)
        values['CtxShadow'] = '0%1X000000' % (values['Ctx_shadow'])

        # A list of all properties we are goind to encode.
        params = ["CtxCfgPresent", "CtxCfgFlags1", "CtxCallback", "CtxShadow",
                "CtxMaxConnectionTime", "CtxMaxDisconnectionTime", "CtxKeyboardLayout",
                "CtxMinEncryptionLevel", "CtxWorkDirectory", "CtxNWLogonServer", "CtxWFHomeDir",
                "CtxWFHomeDirDrive", "CtxWFProfilePath", "CtxInitialProgram", "CtxCallbackNumber",
                "CtxMaxIdleTime"]

        # Convert integer values to string before converting them
        for entry in ['CtxMinEncryptionLevel', 'Ctx_shadow']:
            values[entry] = str(values[entry])

        # Convert each param into an sambaMungedDial style value.
        result_tmp = ""
        for name in params:
            value = values[name]
            is_str = False

            # Special handling for strings and timeParams
            if name in SambaMungedDial.stringParams:
                is_str = True
                value += '\0'
                value = value.encode('utf-16')[2:]
            elif name in SambaMungedDial.timeParams:

                # Convert numerical value back to into mungedDial style.
                usec = int(value) * 60 * 1000
                src = '%04x%04x' % (usec & 0x0FFFF, (usec & 0x0FFFF0000) >> 16)
                value = src[2:4] + src[0:2] + src[6:8] + src[4:6]

            # Append encoded samba attribute to the result.
            m = SambaMungedDial.munge(name, value, is_str)
            result_tmp += m

        # First add the number of attributes
        result = unhexlify(SambaMungedDial.new_header)
        result += unhexlify('%02x00' % (len(params),))
        result += result_tmp
        result = b64encode(result)
        return result

    @staticmethod
    def munge(name, value, isString=False):
        """
        Encodes the given property name and value into a valid
        format for the sambaMungedDial attribute.

        =========== ===============================
        Key         Description
        =========== ===============================
        name        The name of the property to encode
        value       The value of the property
        isString    Boolean, tells whether to encode a string value or not.
        =========== ===============================
        """

        # Encode parameter name with utf-16 and reomve the 2 Byte BOM infront of the string.
        utfName = name.encode('utf-16')[2:]

        # Set parameter length, high and low byte
        paramLen = len(utfName)
        result = ''
        result += chr(paramLen & 0x0FF)
        result += chr((paramLen & 0x0FF00) >> 8)

        # String parameters have additional trailing bytes
        valueLen = len(value)
        result += chr(valueLen & 0x0FF)
        result += chr((valueLen & 0x0FF00) >> 8)

        # Length fields have a trailing '01' appended by the UTF-16 converted name
        result += unhexlify('%02x00' % (0x1,))
        result += utfName

        # Append a trailing '00' to string parameters
        if isString and len(value):
            result += hexlify(value.decode('utf-16'))
        else:
            result += value

        return result

    @staticmethod
    def decode(mstr):
        """
        Decodes a given sambaMungedDial attribute into a human readable
        list of properties.

        =========== ===============================
        Key         Description
        =========== ===============================
        mstr        The b64encoded sambaMungedDial string.
        =========== ===============================
        """

        # check if we've to use the old or new munged dial storage behavior
        test = b64decode(mstr)
        old_behavior = hexlify(test)[0:2] == "6d"
        if old_behavior:
            ctxField = test[len(unhexlify(SambaMungedDial.old_header))::]
        else:
            ctxField = test[len(unhexlify(SambaMungedDial.new_header)) + 2::]

        # Decode parameters
        result = {'oldStorageBehavior': True}
        while ctxField != "":

            # Get parameter-name length and parameter value length
            ctxParmNameLength = ord(ctxField[0]) + (16 * ord(ctxField[1]))
            ctxParmLength = ord(ctxField[2]) + (16 * ord(ctxField[3]))

            # Reposition ctxField on start of parameter name, read parameter name
            ctxField = ctxField[6::]
            ctxParmName = ctxField[0:ctxParmNameLength].decode('utf-16')

            # Reposition ctxField on start of parameter
            ctxField = ctxField[ctxParmNameLength::]
            ctxParm = ctxField[0:ctxParmLength]

            # If string parameter, convert
            if ctxParmName in SambaMungedDial.stringParams:
                ctxParm = unicode(unhexlify(ctxParm))
                if ctxParm[-1] == '\0':
                    ctxParm = ctxParm[:-1]

            # If time parameter, convert
            if ctxParmName in SambaMungedDial.timeParams:
                lo = ctxParm[0:4]
                hi = ctxParm[4:8] * 256
                usecs = (int(lo[2:4], 16) * 256) + (int(lo[0:2], 16)) + (int(hi[2:4], 16) * 256) + (int(hi[0:2], 16) * 256 * 256)
                ctxParm = usecs / (60 * 1000)

            # Assign in result array
            result[ctxParmName] = ctxParm

            # Reposition ctxField on end of parameter and continue
            ctxField = ctxField[ctxParmLength::]

        # Detect TS Login Flag
        flags = ord(result['CtxCfgFlags1'][5])
        result[u'Ctx_flag_tsLogin'] = bool(flags & 1)
        result[u'Ctx_flag_reConn'] = bool(flags & 2)
        result[u'Ctx_flag_brokenConn'] = bool(flags & 4)
        result[u'Ctx_flag_inheritMode'] = bool(result['CtxCfgFlags1'][6:7] == "1")

        # convert the shadow value into integer.
        if old_behavior:
            result[u'Ctx_shadow'] = int(result['CtxCfgFlags1'][1:2])
        else:
            result[u'Ctx_shadow'] = int(result['CtxShadow'][1:2])

        # Convert flags into boolean values.
        connections = int(result['CtxCfgFlags1'][2:3], 16)
        result[u'Ctx_flag_connectClientDrives'] = bool(connections & 8)
        result[u'Ctx_flag_connectClientPrinters'] = bool(connections & 4)
        result[u'Ctx_flag_defaultPrinter'] = bool(connections & 2)

        # Convert integer values to integer
        result['Ctx_shadow'] = int(result['Ctx_shadow'])
        try:
            result['CtxMinEncryptionLevel'] = int(result['CtxMinEncryptionLevel'])
        except:
            result['CtxMinEncryptionLevel'] = 0

        return result
