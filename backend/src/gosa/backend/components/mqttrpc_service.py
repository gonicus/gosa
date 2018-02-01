# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import logging
import sys
import traceback
from lxml import objectify, etree
from tornado import gen
from tornado.concurrent import is_future

from zope.interface import implementer

from gosa.common import Environment
from gosa.common.components import PluginRegistry
from gosa.common.components.jsonrpc_utils import BadServiceRequest
from gosa.common.components.mqtt_handler import MQTTHandler
from gosa.common.gjson import loads, dumps
from gosa.common.error import GosaErrorHandler as C
from gosa.common.handler import IInterfaceHandler
from gosa.common.utils import stripNs


@implementer(IInterfaceHandler)
class MQTTRPCService(object):
    """
    The ProxyServer handles to the RPC calls from the GOsa proxies received via MQTT
    """
    mqtt = None
    _priority_ = 10
    __command_registry = None

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.subtopic = "%s/proxy" % self.env.domain
        self.mqtt = MQTTHandler(host=self.env.config.get("mqtt.host"),
                                port=self.env.config.getint("mqtt.port", default=1883))

    def serve(self):
        self.mqtt.get_client().add_subscription('%s/#' % self.subtopic, qos=2)
        self.mqtt.set_subscription_callback(self.handle_request)
        self.__command_registry = PluginRegistry.getInstance('CommandRegistry')
        self.log.info("MQTT RPC service started, listening on subtopic '%s/#'" % self.subtopic)

    @gen.coroutine
    def handle_request(self, topic, message):
        if topic == self.subtopic:
            # event from proxy received
            try:
                data = etree.fromstring(message, PluginRegistry.getEventParser())
                event_type = stripNs(data.xpath('/g:Event/*', namespaces={'g': "http://www.gonicus.de/Events"})[0].tag)
                if event_type == "ClientLeave":
                    proxy_id = str(data.ClientLeave.Id)
                    registry = PluginRegistry.getInstance("BackendRegistry")
                    registry.unregisterBackend(proxy_id)

            except etree.XMLSyntaxError as e:
                self.log.error("Event parsing error: %s" % e)

        elif topic.startswith(self.subtopic):
            response_topic = "%s/response" % "/".join(topic.split("/")[0:4])

            try:
                id_, res = self.process(topic, message)
                if is_future(res):
                    res = yield res
                response = dumps({"result": res, "id": id_})
                self.log.debug("MQTT-RPC response: %s on topic %s" % (response, topic))

            except Exception as e:
                err = str(e)
                self.log.error("MQTT RPC call error: %s" % err)
                response = dumps({'id': topic.split("/")[-2], 'error': err})

            # Get rid of it...
            self.mqtt.send_message(response, topic=response_topic, qos=2)

        else:
            self.log.warning("unhandled topic request received: %s" % topic)

    def process(self, topic, message):

        try:
            req = loads(message)
        except ValueError as e:
            raise ValueError(C.make_error("INVALID_JSON", data=str(e)))

        try:
            id_ = req['id']
            name = req['method']
            args = req['params']
            kwargs = req['kwparams']
            user = req['user'] if 'user' in req else topic.split("/")[2]
            sid = req['session_id'] if 'session_id' in req else None

        except KeyError as e:
            self.log.error("KeyError: %s" % e)
            raise BadServiceRequest(message)

        self.log.debug("received call [%s] for %s: %s(%s,%s)" % (id_, topic, name, args, kwargs))

        try:
            return id_, self.__command_registry.dispatch(user, sid, name, *args, **kwargs)
        except Exception as e:
            # Write exception to log
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.log.error("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            raise e