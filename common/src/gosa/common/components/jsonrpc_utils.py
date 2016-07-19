# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import datetime
import json
import pkg_resources
import inspect
import base64

json_handlers = {}


class JSONRPCException(Exception):
    """
    Exception raises if there's an error when processing JSONRPC related
    tasks.
    """
    def __init__(self, rpcError):
        super(JSONRPCException, self).__init__(rpcError)
        self.error = rpcError


class ServiceException(Exception):
    pass


class ServiceRequestNotTranslatable(ServiceException):
    pass


class BadServiceRequest(ServiceException):
    pass


class JSONDataHandler(object):

    @staticmethod
    def encode(data):
        raise NotImplementedError("JSONDataHandler implementation fails to encode")

    @staticmethod
    def decode(data):
        raise NotImplementedError("JSONDataHandler implementation fails to decode")

    @staticmethod
    def isinstance(data):
        raise NotImplementedError("JSONDataHandler implementation fails to detect")

    @staticmethod
    def canhandle():
        raise NotImplementedError("JSONDataHandler implementation fails to commit")


class DateTimeDateHandler(JSONDataHandler):

    @staticmethod
    def encode(data):
        if isinstance(data, datetime.datetime):
            data = data.date()
        return  {'object': str(data), '__jsonclass__': 'datetime.date'}

    @staticmethod
    def decode(data):
        return datetime.datetime.strptime(data['object'].split(".")[0], "%Y-%m-%d").date()

    @staticmethod
    def isinstance(data):
        return type(data) == datetime.date

    @staticmethod
    def canhandle():
        return "datetime.date"


class BinaryHandler(JSONDataHandler):

    @staticmethod
    def encode(data):
        return  {'object': data.encode(), '__jsonclass__': 'json.Binary'}

    @staticmethod
    def decode(data):
        return Binary(base64.b64decode(data['object']))

    @staticmethod
    def isinstance(data):
        return isinstance(data, Binary)

    @staticmethod
    def canhandle():
        return "json.Binary"


class DateTimeHandler(JSONDataHandler):

    @staticmethod
    def encode(data):
        return  {'object': str(data), '__jsonclass__': 'datetime.datetime'}

    @staticmethod
    def decode(data):
        return datetime.datetime.strptime(data['object'].split(".")[0], "%Y-%m-%d %H:%M:%S")

    @staticmethod
    def isinstance(data):
        return type(data) == datetime.datetime

    @staticmethod
    def canhandle():
        return "datetime.datetime"


class FactoryHandler(JSONDataHandler):

    @staticmethod
    def encode(data):
        # Just pass-thru, openObject generates the relevant information
        return  data

    @staticmethod
    def decode(data):
        # This is a hack to get a top level proxy with the same
        # parameters that were used to call ourselves.
        for base in inspect.stack():
            if base[3] == "__call__" and 'self' in base[0].f_locals:
                if hasattr(base[0].f_locals['self'], 'getProxy'):
                    proxy = base[0].f_locals['self'].getProxy()

                    jc = data["__jsonclass__"][1]
                    del data["__jsonclass__"]

                    # Extract property presets
                    dat = {}
                    for prop in data:
                        dat[prop] = data[prop]

                    jc.insert(0, proxy)
                    jc.append(dat)

                    from gosa.common.components.jsonrpc_proxy import JSONObjectFactory
                    return JSONObjectFactory.get_instance(*jc)

        raise NotImplementedError("Proxy does not support the getProxy() method")

    @staticmethod
    def isinstance(data):
        # Never detect, openObject generates the relevant information
        return False

    @staticmethod
    def canhandle():
        return "json.JSONObjectFactory"


class PObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        for handler in json_handlers.values():
            if handler.isinstance(obj):
                return handler.encode(obj)

        print("no", obj, type(obj))

        return json.JSONEncoder.default(self, obj)


def PObjectDecoder(dct):
    if '__jsonclass__' in dct:
        clazz = dct['__jsonclass__']
        if type(clazz) == list:
            clazz = clazz[0]

        if clazz in json_handlers:
            return json_handlers[clazz].decode(dct)

        raise NotImplementedError("type '%s' is not serializeable" % clazz)

    return dct


class Binary(object):

    def __init__(self, data):
        self.set(data)

    def __eq__(self, other):
        if isinstance(other, Binary):
            return self.data == other.data
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def set(self, data):
        self.data = data

    def get(self):
        return self.data

    def encode(self):
        return base64.b64encode(self.data)


# Load our entrypoints
for entry in pkg_resources.iter_entry_points("gosa.json.datahandler"):
    mod = entry.load()
    json_handlers[mod.canhandle()] = mod
