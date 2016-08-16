# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import logging
import re
from gosa.common import Environment
import tornado.web
from gosa.backend.utils.ldap import check_auth
import paho.mqtt.client as mqtt
from gosa.common.components import PluginRegistry


class BaseMosquittoClass(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseMosquittoClass, self).__init__(application, request, **kwargs)
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

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
        password = self.get_argument('password')
        is_allowed = False
        is_backend = False
        if hasattr(self.env, "core_uuid") and hasattr(self.env, "core_key"):
            # backend self authentification mode
            is_backend = username == self.env.core_uuid and password == self.env.core_key
            is_allowed = is_backend or check_auth(username, password)
        else:
            is_allowed = check_auth(username, password)
        self.log.debug("MQTT AUTH request from '%s' ['%s'] => %s" %
                       (username, "backend" if is_backend else "client", "GRANTED" if is_allowed else "DENIED"))
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

        is_backend = hasattr(self.env, "core_uuid") and uuid == self.env.core_uuid

        client_channel = "%s/client/%s" % (self.env.domain, uuid)
        event_channel = "%s/events" % self.env.domain

        is_allowed = False

        if is_backend:
            client_channel = "%s/client/+" % self.env.domain
            if topic == event_channel:
                # backend can publish/subscribe to event channel
                is_allowed = True
            elif topic == "%s/client/broadcast" % self.env.domain:
                # backend can publish/subscribe on client broadcast channel
                is_allowed = True
            elif mqtt.topic_matches_sub(client_channel, topic):
                # backend can publish/subscribe (send ClientPoll, receive ClientPing)
                is_allowed = True
            elif topic.startswith("%s/client/" % self.env.domain) and topic.endswith("/to-client"):
                # the temporary RPC to-client channel: backend can send
                is_allowed = acc == "2"
            elif topic.startswith("%s/client/" % self.env.domain) and topic.endswith("/to-backend"):
                # the temporary RPC to-backend channel: backend can receive
                is_allowed = acc == "1"
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
            elif topic.startswith("%s/client/" % self.env.domain) and topic.endswith("/to-client"):
                # the temporary RPC to-client channel: client can subscribe
                is_allowed = acc == "1"
            elif topic.startswith("%s/client/" % self.env.domain) and topic.endswith("/to-backend"):
                # the temporary RPC to-backend channel: client can publish
                is_allowed = acc == "2"
            else:
                is_allowed = False

        self.log.debug("MQTT ACL request: '%s'|->%s from '%s' ['%s'] => %s" %
                       (topic, "PUB" if acc == "2" else "SUB" if acc == "1" else "BOTH" if acc == "0" else "UNKOWN",
                        uuid, "backend" if is_backend else "client", "GRANTED" if is_allowed else "DENIED"))
        self.send_result(is_allowed)


class MosquittoSuperuserHandler(BaseMosquittoClass):
    """
    Handles Mosquitto auth plugins http superuser authentication requests
    """

    def post(self, *args, **kwargs):
        self.send_result(False)
