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

from zope.interface import implementer

from gosa.common import Environment
from gosa.common.components import PluginRegistry
from gosa.common.components.jsonrpc_utils import BadServiceRequest
from gosa.common.components.mqtt_handler import MQTTHandler
from gosa.common.gjson import loads, dumps
from gosa.common.error import GosaErrorHandler as C
from gosa.common.handler import IInterfaceHandler


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
        self.mqtt = MQTTHandler(host=self.env.config.get("backend.mqtt-host"),
                                port=self.env.config.getint("backend.mqtt-port", default=1883))

    def serve(self):
        self.mqtt.get_client().add_subscription('%s/#' % self.subtopic)
        self.mqtt.set_subscription_callback(self.__handle_request)
        self.__command_registry = PluginRegistry.getInstance('CommandRegistry')
        self.log.info("MQTT RPC service started, listening on subtopic '%s/#'" % self.subtopic)

    def __handle_request(self, topic, message):
        if topic.startswith(self.subtopic):
            response_topic = "%s/response" % "/".join(topic.split("/")[0:4])

            try:
                id_, res = self.process(topic, message)
                response = dumps({"result": res, "id": id_})

            except Exception as e:
                err = str(e)
                self.log.error("MQTT RPC call error: %s" % err)
                response = dumps({'id': topic.split("/")[-2], 'error': err})

            # Get rid of it...
            self.mqtt.send_message(response, topic=response_topic)

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
            user = req['user'] if 'user' in req else topic.split("/")[2]
            sid = req['session_id'] if 'session_id' in req else None

        except KeyError as e:
            self.log.error("KeyError: %s" % e)
            raise BadServiceRequest(message)

        self.log.debug("received call [%s] for %s: %s(%s)" % (id_, topic, name, args))

        try:
            return id_, self.__command_registry.dispatch(user, sid, name, *args)
        except Exception as e:
            # Write exception to log
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.log.error("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            raise e