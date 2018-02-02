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
from gosa.common.gjson import loads, dumps
from tornado.queues import Queue, QueueEmpty
from tornado import gen
from gosa.common import Environment
from gosa.common.components import JSONRPCException, PluginRegistry


class BaseClient(mqtt.Client):  # pragma: nocover
    _clients = []

    def __init__(self, client_id=None, clean_session=True, userdata=None, protocol=mqtt.MQTTv31):
        super(BaseClient, self).__init__(client_id=client_id, clean_session=clean_session, userdata=userdata, protocol=protocol)
        BaseClient._clients.append(self)

    def get_thread(self):
        return self._thread

    @classmethod
    def get_clients(cls):
        return cls._clients

    def get_client_id(self):
        return self._client_id


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
        >>> client.publish('/topic/to/publish', 'my message')
    """
    __published_messages = {}
    __sync_message_queues = {}
    __sender_id = None
    __connection_retries = 3
    __connection_retry_delay = 3
    __retried = 0

    def __init__(self, host, port=1883, keepalive=60, use_ssl=None, ca_file=None, insecure=None):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

        self.connected = False

        self.client = BaseClient()
        self.host = host
        self.port = port
        self.keepalive = keepalive

        # set the callbacks
        self.client.on_connect = self.__on_connect
        self.client.on_message = self.__on_message
        self.client.on_subscribe = self.__on_subscribe
        self.client.on_unsubscribe = self.__on_unsubscribe
        self.client.on_publish = self.__on_publish
        self.client.on_log = self.__on_log
        if insecure is None:
            insecure = self.env.config.getboolean('mqtt.insecure')

        use_ssl = use_ssl if use_ssl is not None else self.env.config.getboolean('mqtt.ssl')
        if use_ssl is False and not self.env.config.has('mqtt.ssl'):
            # fallback to http.ssl setting
            use_ssl = self.env.config.getboolean('http.ssl')

        if use_ssl is True:
            cert = ca_file if ca_file is not None else self.env.config.get('mqtt.ca_file', default=None)
            if cert is not None:
                self.client.tls_set(cert)
                self.client.tls_insecure_set(insecure)

        self.subscriptions = {}

    def __on_log(self, client, userdata, level, buf):
        self.log.debug("%s: MQTT-log message: %s" % (self.__get_identifier(), buf))

    def authenticate(self, uuid, secret=None):
        """ Send credentials to the MQTT broker.
        Note: must be called before connecting """
        self.__sender_id = uuid
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
        self.client.loop_start()
        self.env.threads.append(self.client.get_thread())

    def reconnect(self):
        self.client.reconnect()

    def disconnect(self):
        """ disconnect from the MQTT broker """
        self.client.disconnect()
        self.client.loop_stop()
        self.__sender_id = None

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
            self.log.debug("%s: subscribing to '%s' => mid: '%s' == '%s'" % (self.__get_identifier(), topic, mid, res))
            self.subscriptions[topic]['mid'] = mid
            self.subscriptions[topic]['subscription_result'] = res

    def __get_identifier(self):
        """
        generates an identifier by combining the broker host
        and the client_id. Used mainly as preix for log messages
        """
        return "%s:%s/%s" % (self.host, self.port, self.client.get_client_id())

    def set_subscription_callback(self, callback):
        """ set a general callback for all subscriptions """
        for topic in self.subscriptions:
            self.subscriptions[topic]['callback'] = callback

    def __on_subscribe(self, client, userdata, mid, granted_qos):
        self.log.debug("%s: on_subscribe client='%s', userdata='%s', mid='%s', granted_qos='%s'" % (self.__get_identifier(), client, userdata, mid, granted_qos))
        for topic in self.subscriptions:
            if 'mid' in self.subscriptions[topic] and self.subscriptions[topic]['mid'] == mid:
                self.subscriptions[topic]['granted_qos'] = granted_qos
                self.subscriptions[topic]['subscribed'] = True

    def __on_unsubscribe(self, client, userdata, mid):
        self.log.debug("%s: on_unsubscribe client='%s', userdata='%s', mid='%s'" % (self.__get_identifier(), client, userdata, mid))
        for topic in list(self.subscriptions):
            if 'mid' in self.subscriptions[topic] and self.subscriptions[topic]['mid'] == mid:
                del self.subscriptions[topic]

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
            self.log.info("%s: MQTT successfully connected" % self.__get_identifier())
            self.connected = True
            self.__retried = 0
            for topic in self.subscriptions.keys():
                (res, mid) = self.client.subscribe(topic)
                self.log.debug("%s: subscribing to '%s' => mid: '%s' == '%s'" % (self.__get_identifier(), topic, mid, res))
                self.subscriptions[topic]['mid'] = mid
                self.subscriptions[topic]['subscription_result'] = res
        else:
            msg = mqtt.error_string(rc)
            self.log.error("%s: MQTT connection error: %s" % (self.__get_identifier(), msg))
            self.__reconnect()

    @gen.coroutine
    def __reconnect(self):
        if self.__retried < self.__connection_retries:
            yield gen.sleep(self.__connection_retry_delay)
            if self.connected is False:
                self.__retried += 1
                self.log.debug("%s: Reconnecting retry %s to %s" % (self.__get_identifier(), self.__retried, self.host))
                self.reconnect()

    def __on_message(self, client, userdata, message):
        payload = loads(message.payload)
        if isinstance(payload, dict) and "content" in payload:
            content = payload["content"]
            if self.__sender_id is not None and 'sender_id' in payload and payload['sender_id'] == self.__sender_id:
                # skip own messages
                return
        else:
            content = payload

        subs = self.get_subscriptions(message.topic)
        for sub in subs:
            if sub['sync'] is True:
                self.log.debug("%s: incoming message for synced topic %s" % (self.__get_identifier(), message.topic))
                self.__sync_message_queues[message.topic].put(content)
            if 'callback' in sub and sub['callback'] is not None:
                callback = sub['callback']
                callback(message.topic, content)
        if len(subs) == 0:
            self.log.warning("Incoming message for unhandled topic '%s'" % message.topic)

    @gen.coroutine
    def get_sync_response(self, topic, message, qos=0):
        """
        Sends a message to a client queue and waits and returns the response from the client.

        :param topic: Topic this message should be sent to / received from
        :param message: The message published on the request topic
        :param qos: QOS value
        :return: The clients response
        """
        # listen on the backend response topic
        listen_to_topic = "%s/response" % topic
        self.__sync_message_queues[listen_to_topic] = Queue()
        self.add_subscription(listen_to_topic, sync=True)
        self.publish("%s/request" % topic, message, qos)
        # send to the client topic
        try:
            response = yield self.__sync_message_queues[listen_to_topic].get(timeout=datetime.timedelta(seconds=10))
            self.__sync_message_queues[listen_to_topic].task_done()
            return response
        except QueueEmpty:
            raise JSONRPCException("Timeout while waiting for the clients response")
        finally:
            self.remove_subscription(listen_to_topic)

    @gen.coroutine
    def publish(self, topic, message, qos=0, retain=False, retried=0):
        """ Publish a message on the MQTT bus"""
        message = {
            "sender_id": self.__sender_id,
            "content": message
        }
        res, mid = self.client.publish(topic, payload=dumps(message), qos=qos, retain=retain)

        self.__published_messages[mid] = res
        if res == mqtt.MQTT_ERR_NO_CONN:
            self.log.error("%s: mqtt server not reachable, message could not be send to '%s'" % (self.__get_identifier(), topic))

            if qos > 0 and retried < 3:
                # try again
                yield gen.sleep(0.1)
                self.publish(topic, message, qos=qos, retain=retain, retried=retried+1)

    def will_set(self, topic, message, qos=0, retain=False):
        """
        Set a Will to be sent to the broker. If the client disconnects without calling disconnect(),
        the broker will publish the message on its behalf.
        """
        payload = {
            "content": message,
            "sender_id": self.__sender_id
        }
        self.client.will_set(topic, dumps(payload), qos, retain)

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
