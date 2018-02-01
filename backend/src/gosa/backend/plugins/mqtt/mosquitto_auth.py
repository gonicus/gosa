# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import logging

from gosa.backend.utils import BackendTypes
from gosa.common import Environment
from gosa.backend.utils.ldap import check_auth
import paho.mqtt.client as mqtt
from gosa.common.components import PluginRegistry
from gosa.common.hsts_request_handler import HSTSRequestHandler


class BaseMosquittoClass(HSTSRequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseMosquittoClass, self).__init__(application, request, **kwargs)
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.superuser = self.env.config.get("mqtt.superuser")
        self.backend_registry = PluginRegistry.getInstance("BackendRegistry")

    def initialize(self):
        self.set_header('Content-Type', 'text/plain')
        self.set_header('Cache-Control', 'no-cache')

    def send_result(self, result):
        if result is True:
            self.set_status(200)
        else:
            self.set_status(403)
        self.finish('')

    def check_xsrf_cookie(self):  # pragma: nocover
        pass

    def data_received(self, chunk):  # pragma: nocover
        pass


class MosquittoAuthHandler(BaseMosquittoClass):
    """
    Handles Mosquitto auth plugins http authentification requests and checks them against ldap
    """

    def post(self, *args, **kwargs):
        username = self.get_argument('username', '')
        if self.superuser is not None and username == self.superuser:
            self.log.debug("MQTT AUTH request from '%s' [SUPERUSER] => GRANTED" % username)
            self.send_result(True)
        else:
            password = self.get_argument('password')

            # backend self authentification mode
            is_backend = self.backend_registry.check_auth(username, password)
            backend_type = self.backend_registry.get_type(username)
            is_allowed = is_backend or check_auth(username, password)
            self.log.debug("MQTT AUTH request from '%s' ['%s'] => %s" %
                           (username, backend_type if backend_type is not None else "client", "GRANTED" if is_allowed else "DENIED"))
            self.send_result(is_allowed)


class MosquittoAclHandler(BaseMosquittoClass):
    """
    Handles Mosquitto auth plugins http authorization (ACL) requests
    """

    def post(self, *args, **kwargs):
        """
        Handle incoming acl post request from the mosquitto auth plugin.
        Available parameters are:
            username: current username
            topic: mqtt topic
            clientid: client id
            acc: (1 == subscribe, 2 == publish)
        """
        uuid = self.get_argument('username', '')
        topic = self.get_argument('topic')
        # 1 == SUB, 2 == PUB
        acc = self.get_argument('acc')

        backend_type = self.backend_registry.get_type(uuid)

        client_channel = "%s/client/%s" % (self.env.domain, uuid)
        event_channel = "%s/events" % self.env.domain

        if topic == "%s/bus" % self.env.domain:
            # internal communication topic everyone can pub/sub to
            is_allowed = True

        elif backend_type is not None:
            client_channel = "%s/client/+" % self.env.domain
            if topic == event_channel:
                # backend can publish/subscribe to event channel
                is_allowed = True
            elif topic == "%s/client/broadcast" % self.env.domain:
                # backend can publish/subscribe on client broadcast channel
                is_allowed = True
            elif topic == "%s/client/#" % self.env.domain:
                # proxy can publish/subscribe on all client subtopics
                is_allowed = backend_type == BackendTypes.proxy
            elif topic == "%s/proxy" % self.env.domain:
                # proxy and backend can publish/subscribe on /proxy topic
                is_allowed = True
            elif mqtt.topic_matches_sub(client_channel, topic):
                # backend can publish/subscribe (send ClientPoll, receive ClientPing)
                is_allowed = True
            elif topic.startswith("%s/client/" % self.env.domain) and topic.endswith("/request"):
                # the temporary RPC request channel: backend can send
                is_allowed = acc == "2"
            elif topic.startswith("%s/client/" % self.env.domain) and topic.endswith("/response"):
                # the temporary RPC response channel: backend can receive
                is_allowed = acc == "1"
            elif topic.startswith("%s/proxy/" % self.env.domain) and topic.endswith("/request"):
                # the temporary RPC request channel from proxy: backend can receive, proxy can publish
                if backend_type == BackendTypes.proxy:
                    is_allowed = acc == "2"
                else:
                    is_allowed = acc == "1"
            elif topic.startswith("%s/proxy/" % self.env.domain) and topic.endswith("/response"):
                # the temporary RPC response channel to proxy: backend can publish, proxy can receive
                if backend_type == BackendTypes.proxy:
                    is_allowed = acc == "1"
                else:
                    is_allowed = acc == "2"
            else:
                is_allowed = False
        else:
            if topic == event_channel:
                # global event topic -> check acls
                acl = PluginRegistry.getInstance("ACLResolver")
                topic = ".".join([self.env.domain, 'event'])
                is_allowed = acl.check(uuid, topic, "x")
            elif topic == "%s/client/broadcast" % self.env.domain:
                # client can listen on client broadcast channel
                is_allowed = acc == "1"
            elif topic == client_channel:
                # client can do both on own channel
                is_allowed = True
            elif topic.startswith("%s/proxy/" % self.env.domain) and topic.endswith("/request"):
                # relayed request client -> proxy -> backend: client can publish
                is_allowed = acc == "2"
            elif topic.startswith("%s/proxy/" % self.env.domain) and topic.endswith("/response"):
                # relayed response backend -> proxy -> client: client can subscribe
                is_allowed = acc == "1"
            elif topic.startswith("%s/client/" % self.env.domain) and topic.endswith("/request"):
                # the temporary RPC request channel: client can subscribe
                is_allowed = acc == "1"
            elif topic.startswith("%s/client/" % self.env.domain) and topic.endswith("/response"):
                # the temporary RPC response channel: client can publish
                is_allowed = acc == "2"
            else:
                is_allowed = False

        self.log.debug("MQTT ACL request: '%s'|->%s from '%s' ['%s'] => %s" %
                       (topic, "PUB" if acc == "2" else "SUB" if acc == "1" else "BOTH" if acc == "0" else "UNKOWN",
                        uuid, backend_type if backend_type is not None else "client", "GRANTED" if is_allowed else "DENIED"))
        self.send_result(is_allowed)


class MosquittoSuperuserHandler(BaseMosquittoClass):
    """
    Handles Mosquitto auth plugins http superuser authentication requests
    """

    def post(self, *args, **kwargs):
        if self.superuser is not None:
            is_allowed = self.get_argument('username', '') == self.superuser
            self.log.debug("MQTT Superuser ACL request for '%s': %s" % (self.get_argument('username', ''), "GRANTED" if is_allowed else "DENIED"))
            self.send_result(self.get_argument('username', '') == self.superuser)
        else:
            self.send_result(False)
