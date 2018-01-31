# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import uuid
from tornado import gen

from gosa.common import Environment
from gosa.common.components.json_exception import JSONRPCException
from gosa.common.components.mqtt_handler import MQTTHandler
from gosa.common.gjson import dumps, loads
from tornado.concurrent import Future


class MQTTException(Exception):
    pass


class MQTTServiceProxy(object):
    """
    The MQTTServiceProxy provides a simple way to use GOsa RPC
    services from various clients. Using the proxy object, you
    can directly call methods without the need to know where
    it actually gets executed::

        >>> from gosa.common.components.mqtt_proxy import MQTTServiceProxy
        >>> proxy = MQTTServiceProxy('localhost')
        >>> proxy.getMethods()

    This will return a dictionary describing the available methods.

    =============== ============
    Parameter       Description
    =============== ============
    mqttHandler     MQTTHandler used to connect to the MQTT service broker
    serviceAddress  Address string describing the target queue to bind to, must be skipped if no special queue is needed
    serviceName     *internal*
    methods         *internal*
    =============== ============

    The MQTTService proxy creates a temporary MQTT *reply to* queue, which
    is used for command results.
    """
    worker = {}

    def __init__(self, mqttHandler=None, serviceAddress=None, serviceName=None,
                 methods=None):
        self.__handler = mqttHandler if mqttHandler is not None else MQTTHandler()
        self.__serviceName = serviceName
        self.__serviceAddress = serviceAddress
        self.__methods = methods
        self.env = Environment.getInstance()

        # Retrieve methods
        if self.__methods is None:
            self.__serviceName = "getMethods"
            self.__methods = self.__call__()
            self.__serviceName = None

    #pylint: disable=W0613
    def login(self, user, password):  # pragma: nocover
        return True

    def logout(self):  # pragma: nocover
        return True

    def close(self):  # pragma: nocover
        pass

    def getProxy(self):
        return MQTTServiceProxy(self.__handler, self.__serviceAddress, None, methods=self.__methods)

    def __getattr__(self, name):
        if self.__serviceName is not None:
            name = "%s/%s" % (self.__serviceName, name)

        return MQTTServiceProxy(self.__handler, self.__serviceAddress, name, methods=self.__methods)

    @gen.coroutine
    def __call__(self, *args, **kwargs):
        data = {}
        if '__user__' in kwargs:
            data['user'] = kwargs['__user__']
            del kwargs['__user__']
        if '__session_id__' in kwargs:
            data['session_id'] = kwargs['__session_id__']
            del kwargs['__session_id__']

        # Default to 'core' queue
        call_id = uuid.uuid4()
        topic = "%s/%s" % (self.__serviceAddress, call_id)

        if isinstance(self.__methods, Future):
            self.__methods = yield self.__methods

        if self.__methods and self.__serviceName not in self.__methods:
            raise NameError("name '%s' not defined" % self.__serviceName)

        # Send
        data.update({
            "method": self.__serviceName,
            "id": "jsonrpc",
            "sender": self.env.uuid
        })
        data["kwparams"] = kwargs
        data["params"] = args
        postdata = dumps(data)

        response = yield self.__handler.send_sync_message(postdata, topic)
        resp = loads(response)

        if 'error' in resp and resp['error'] is not None:
            raise JSONRPCException(resp['error'])

        return resp['result']

