# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import logging
import datetime
import paho.mqtt.client as mqtt
from tornado.queues import Queue, QueueEmpty
from tornado import gen
from gosa.common import Environment
from gosa.common.components import JSONRPCException


class BaseClient(mqtt.Client):

    def __init__(self):
        super(BaseClient, self).__init__()

    def get_thread(self):
        return self._thread


class MQTTClient(object):
    """
    The MQTTClient is responsible for the connection to a MQTT broker (Mosquitto)
    Usage example:
        >>> from gosa.common.components.mqtt_client import MQTTClient
        >>>
        >>> def my_callback(topic, message):
        >>>     print("Message: %s, Topic: %s" % (message, topic))
        >>>
        >>> client = MQTTClient('localhost')
        >>> client.connect('username', 'password')
        >>> client.add_subscription('/topic/im/interested/in', callback=my_callback)
        >>> client.publish('/topic/to/pushish', 'my message')
    """
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
        self.loop_forever = loop_forever

        # set the callbacks
        self.client.on_connect = self.__on_connect
        self.client.on_message = self.__on_message
        self.client.on_subscribe = self.__on_subscribe
        self.client.on_unsubscribe = self.__on_unsubscribe
        self.client.on_publish = self.__on_publish
        self.client.on_log = self.__on_log

        self.subscriptions = {}

    def __on_log(self, client, userdata, level, buf):
        self.log.debug("MQTT-log message: %s" % buf)

    def authenticate(self, uuid, secret=None):
        """ Send credentials to the MQTT broker.
        Note: must be called before connecting """
        self.client.username_pw_set(uuid, secret)

    def connect(self, uuid=None, secret=None):
        """
        Connect to the MQTT broker
        :param uuid: username (optional)
        :param secret: password (optional)
        """
        if uuid is not None:
            self.authenticate(uuid, secret)
        self.client.connect(self.host, port=self.port, keepalive=self.keepalive)
        if self.loop_forever is True:
            self.client.loop_forever()
        else:
            self.client.loop_start()
        self.env.threads.append(self.client.get_thread())

    def disconnect(self):
        """ disconnect from the MQTT broker """
        self.client.disconnect()
        self.client.loop_stop()

    def add_subscription(self, topic, callback=None, qos=0, sync=False):
        """ subscribe to a topic """
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
        """ set a general callback for all subscriptions """
        for topic in self.subscriptions:
            self.subscriptions[topic]['callback'] = callback

    def __on_subscribe(self, client, userdata, mid, granted_qos):
        self.log.debug("on_subscribe client='%s', userdata='%s', mid='%s', granted_qos='%s'" % (client, userdata, mid, granted_qos))
        for topic in self.subscriptions:
            if 'mid' in self.subscriptions[topic] and self.subscriptions[topic]['mid'] == mid:
                self.subscriptions[topic]['granted_qos'] = granted_qos
                self.subscriptions[topic]['subscribed'] = True

    def __on_unsubscribe(self, client, userdata, mid):
        self.log.debug("on_unsubscribe client='%s', userdata='%s', mid='%s'" % (client, userdata, mid))
        for topic in self.subscriptions:
            if 'mid' in self.subscriptions[topic] and self.subscriptions[topic]['mid'] == mid:
                self.subscriptions[topic]['subscribed'] = False
                del self.subscriptions[topic]['granted_qos']
                del self.subscriptions[topic]['mid']

    def remove_subscription(self, topic):
        """ unsubscribe from the given topic """
        if topic in self.subscriptions:
            del self.subscriptions[topic]
            if self.connected is True:
                self.client.unsubscribe(topic)

    def clear_subscriptions(self):
        """ unsubscribe from all subscribed topics """
        self.client.unsubscribe(self.subscriptions.keys())

    def __on_connect(self, client, userdata, flags, rc):
        if rc == mqtt.CONNACK_ACCEPTED:
            # connection successful
            self.connected = True
            for topic in self.subscriptions.keys():
                (res, mid) = self.client.subscribe(topic)
                self.log.debug("subscribing to '%s' => mid: '%s' == '%s'" % (topic, mid, res))
                self.subscriptions[topic]['mid'] = mid
                self.subscriptions[topic]['subscription_result'] = res
        else:
            msg = mqtt.error_string(rc)
            self.log.error(msg)

    def __on_message(self, client, userdata, message):
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

    @gen.coroutine
    def get_sync_response(self, topic, message, qos=0):
        """
        Sends a message to a client queue and waits and returns the response from the client.

        :param topic: Topic this message should be sent to / received from
        :param message: The message published on the to-client topic
        :param qos: QOS value
        :return: The clients response
        """
        # listen on the backend response topic
        listen_to_topic = "%s/to-backend" % topic
        self.__sync_message_queues[listen_to_topic] = Queue()
        self.add_subscription(listen_to_topic, sync=True)
        self.publish("%s/to-client" % topic, message, qos)
        # send to the client topic
        try:
            response = yield self.__sync_message_queues[listen_to_topic].get(timeout=datetime.timedelta(seconds=10))
            self.__sync_message_queues[listen_to_topic].task_done()
            raise gen.Return(response)
        except QueueEmpty:
            raise JSONRPCException("Timeout while waiting for the clients response")
        finally:
            self.remove_subscription(listen_to_topic)

    def publish(self, topic, message, qos=0, retain=False):
        """ Publish a message on the MQTT bus"""
        res, mid = self.client.publish(topic, payload=message, qos=qos, retain=retain)

        self.__published_messages[mid] = res
        if res == mqtt.MQTT_ERR_NO_CONN:
            self.log.error("mqtt server not reachable, message could not be send to '%s'" % topic)

    def __on_publish(self, client, userdata, mid):
        if mid in self.__published_messages:
            del self.__published_messages[mid]

    def get_subscriptions(self, topic):
        """
        Find the subscriptions that match the given topic
        :param topic: Topic to check
        :return: list of found subscriptions
        """
        return [self.subscriptions[t] for t in self.subscriptions if mqtt.topic_matches_sub(t, topic)]
