# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

import uuid
from threading import Thread
from queue import Queue
from gosa.common.components.json_exception import JSONRPCException
from gosa.common.components.mqtt_handler import MQTTHandler
from gosa.common.gjson import dumps, loads


class MQTTException(Exception):
    pass


class MQTTServiceProxy(object):
    """
    The MQTTServiceProxy provides a simple way to use clacks RPC
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
    serviceURL      URL used to connect to the MQTT service broker
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
        self.__handler = mqttHandler if isinstance(mqttHandler, MQTTHandler) else MQTTHandler()
        self.__serviceName = serviceName
        self.__serviceAddress = serviceAddress
        self.__methods = methods

        # Retrieve methods
        if not self.__methods:
            self.__serviceName = "getMethods"
            self.__methods = self.__call__()
            self.__serviceName = None

    #pylint: disable=W0613
    def login(self, user, password):
        return True

    def logout(self):
        return True

    def getProxy(self):
        return MQTTServiceProxy(self.__serviceURL,
                self.__serviceAddress,
                None,
                self.__conn,
                methods=self.__methods)

    def __getattr__(self, name):
        if self.__serviceName is not None:
            name = "%s/%s" % (self.__serviceName, name)

        return MQTTServiceProxy(self.__handler, self.__serviceAddress, name, methods=self.__methods)

    def __call__(self, *args, **kwargs):
        if len(kwargs) > 0 and len(args) > 0:
            raise JSONRPCException("JSON-RPC does not support positional and keyword arguments at the same time")

        # Default to 'core' queue
        call_id = uuid.uuid4()
        topic = "%s/%s" % (self.__serviceAddress, call_id)

        if self.__methods and self.__serviceName not in self.__methods:
            raise NameError("name '%s' not defined" % self.__serviceName)

        # Send
        if len(kwargs):
            postdata = dumps({"method": self.__serviceName, 'params': kwargs, 'id': 'jsonrpc'})
        else:
            postdata = dumps({"method": self.__serviceName, 'params': args, 'id': 'jsonrpc'})

        response = self.__handler.send_sync_message(postdata, topic)
        resp = loads(response)

        if 'error' in resp and resp['error'] is not None:
            raise JSONRPCException(resp['error'])

        return resp['result']

