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

import logging
import re

import asyncio
import paho.mqtt.client as mqtt
from queue import Queue, Empty
from gosa.common import Environment
from gosa.common.components import JSONRPCException


class BaseClient(mqtt.Client):

    def __init__(self):
        super(BaseClient, self).__init__()

    def get_thread(self):
        return self._thread


class MQTTClient(object):
    __published_messages = {}
    __sync_message_queues = {}

    def __init__(self, host, port=1883, keepalive=60, loop_forever=False):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

        self.connected = False

        self.client = BaseClient()
        self.host = host
        self.port = port
        self.keepalive = keepalive
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_unsubscribe = self.on_unsubscribe
        self.client.on_publish = self.on_publish
        self.client.on_log = self.on_log
        self.loop_forever = loop_forever

        self.subscriptions = {}

    def on_log(self, client, userdata, level, buf):
        self.log.debug("MQTT-log message: %s" % buf)

    def authenticate(self, uuid, secret=None):
        self.client.username_pw_set(uuid, secret)

    def connect(self, uuid=None, secret=None):
        if uuid is not None:
            self.authenticate(uuid, secret)
        self.client.connect(self.host, port=self.port, keepalive=self.keepalive)
        if self.loop_forever is True:
            self.client.loop_forever()
        else:
            self.client.loop_start()
        self.env.threads.append(self.client.get_thread())

    def disconnect(self):
        self.client.disconnect()
        self.client.loop_stop()

    def add_subscription(self, topic, callback=None, qos=0, sync=False):
        if topic not in self.subscriptions.keys():
            self.subscriptions[topic] = {
                'subscribed': False,
                'qos': qos,
                'callback': callback,
                'sync': sync
            }
        if self.connected is True:
            (res, mid) = self.client.subscribe(topic)
            self.log.debug("subscribing to '%s' => mid: '%s' == '%s'" % (topic, mid, res))
            self.subscriptions[topic]['mid'] = mid
            self.subscriptions[topic]['subscription_result'] = res

    def set_subscription_callback(self, callback):
        for topic in self.subscriptions:
            self.subscriptions[topic]['callback'] = callback

    def on_subscribe(self, client, userdata, mid, granted_qos):
        self.log.debug("on_subscribe client='%s', userdata='%s', mid='%s', granted_qos='%s'" % (client, userdata, mid, granted_qos))
        for topic in self.subscriptions:
            if 'mid' in self.subscriptions[topic] and self.subscriptions[topic]['mid'] == mid:
                self.subscriptions[topic]['granted_qos'] = granted_qos
                self.subscriptions[topic]['subscribed'] = True

    def on_unsubscribe(self, client, userdata, mid):
        self.log.debug("on_unsubscribe client='%s', userdata='%s', mid='%s'" % (client, userdata, mid))
        for topic in self.subscriptions:
            if 'mid' in self.subscriptions[topic] and self.subscriptions[topic]['mid'] == mid:
                self.subscriptions[topic]['subscribed'] = False
                del self.subscriptions[topic]['granted_qos']
                del self.subscriptions[topic]['mid']

    def remove_subscription(self, topic):
        if topic in self.subscriptions:
            del self.subscriptions[topic]
            if self.connected is True:
                self.client.unsubscribe(topic)

    def clear_subscriptions(self):
        self.client.unsubscribe(self.subscriptions.keys())

    def on_connect(self, client, userdata, flags, rc):
        if rc == mqtt.CONNACK_ACCEPTED:
            # connection successful
            self.connected = True
            for topic in self.subscriptions.keys():
                (res, mid) = self.client.subscribe(topic)
                self.log.debug("subscribing to '%s' => mid: '%s' == '%s'" % (topic, mid, res))
                self.subscriptions[topic]['mid'] = mid
                self.subscriptions[topic]['subscription_result'] = res
        else:
            msg = "Connection refused - "
            if rc == mqtt.CONNACK_REFUSED_PROTOCOL_VERSION:
                msg += "incorrect protocol version"
            elif rc == mqtt.CONNACK_REFUSED_IDENTIFIER_REJECTED:
                msg += "invalid client identifier"
            elif rc == mqtt.CONNACK_REFUSED_SERVER_UNAVAILABLE:
                msg += "server unavailable"
            elif rc == mqtt.CONNACK_REFUSED_BAD_USERNAME_PASSWORD:
                msg += "bad username or password"
            elif rc == mqtt.CONNACK_REFUSED_NOT_AUTHORIZED:
                msg += "not authorized"

            self.log.error(msg)

    def on_message(self, client, userdata, message):
        subs = self.get_subscriptions(message.topic)
        for sub in subs:
            if sub['sync'] is True:
                self.log.debug("incoming message for synced topic %s" % message.topic)
                if message.topic not in self.__sync_message_queues:
                    self.__sync_message_queues[message.topic] = Queue()
                self.__sync_message_queues[message.topic].put(message.payload.decode('utf-8'))
            if 'callback' in sub and sub['callback'] is not None:
                callback = sub['callback']
                callback(message.topic, message.payload.decode('utf-8'))
        if len(subs) == 0:
            self.log.warning("Incoming message for unhandled topic '%s'" % message.topic)

    def get_sync_response(self, topic, message, qos=0):
        # listen on the backend response topic
        listen_to_topic = "%s/to-backend" % topic
        self.__sync_message_queues[listen_to_topic] = Queue()
        self.add_subscription(listen_to_topic, sync=True)
        self.publish("%s/to-client" % topic, message, qos)
        # send to the client topic
        try:
            response = self.__sync_message_queues[listen_to_topic].get(True, 10)
            self.__sync_message_queues[listen_to_topic].task_done()
            return response
        except Empty:
            raise JSONRPCException("Timeout while waiting for the clients response")
        finally:
            self.remove_subscription(listen_to_topic)

    def publish(self, topic, message, qos=0, retain=False):
        res, mid = self.client.publish(topic, payload=message, qos=qos, retain=retain)
        self.log.debug("publishing message to '%s', content: '%s'" % (topic, message))

        self.__published_messages[mid] = res
        if res == mqtt.MQTT_ERR_NO_CONN:
            self.log.error("mqtt server not reachable, message could not be send to '%s'" % topic)

    def on_publish(self, client, userdata, mid):
        self.log.debug("on publish message mid '%s' received" % mid)
        if mid in self.__published_messages:
            del self.__published_messages[mid]

    def get_subscriptions(self, topic):
        return [self.subscriptions[t] for t in self.subscriptions if mqtt.topic_matches_sub(t, topic)]
        # for t in self.subscriptions:
        #     match = False
        #     if t[-1] == "#":
        #         match = topic.startswith(t[0:-1])
        #         self.log.debug("%s matches %s => %s" % (t, topic, match))
        #     elif "+" in t:
        #         # use a regex
        #         regex = t.replace("+", "[^\/]+")
        #         if t[-1] == "+":
        #             regex += "$"
        #         p = re.compile(regex)
        #         match = p.match(topic) is not None
        #         self.log.debug("%s matches %s => %s" % (regex, topic, match))
        #     elif t == topic:
        #         match = True
        #         self.log.debug("'%s' equals '%s' => %s" % (t, topic, match))
        #
        #     if match:
        #         subscriptions.append(self.subscriptions[t])
        #
        # return subscriptions
