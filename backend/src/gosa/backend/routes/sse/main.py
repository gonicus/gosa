# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import uuid
import time
import hashlib
import logging

from gosa.common.utils import stripNs, N_
from gosa.common.gjson import dumps
from tornado import web


class SseHandler(web.RequestHandler):
    """
    Server sent event handler based on tornado
    Example for sending events with SSE:

        >>> from gosa.backend.routes.sse.main import SseHandler
        >>>
        >>> # send 'general' message
        >>> SseHandler.send_message("message content")
        >>>
        >>> # send SSE for special event name
        >>> SseHandler.send_message("message content", "event-name")
    """

    _connections = {}
    _channels = {}
    _cache = []
    _cache_size = 200

    def __init__(self, application, request, **kwargs):
        super(SseHandler, self).__init__(application, request, **kwargs)
        self.stream = request.connection.stream
        self._closed = False
        self.log = logging.getLogger(__name__)
        self.channels = []

    def initialize(self):
        self._last = None
        self.set_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.set_header('Cache-Control', 'no-cache')
        self.set_header('Connection', 'keep-alive')

    def set_id(self):
        self.connection_id = hashlib.md5(('%s-%s-%s' % (
            self.request.connection.context.address[0],
            self.request.connection.context.address[1],
            time.time(),
        )).encode('utf-8')).hexdigest()

    @web.asynchronous
    def get(self):
        if self.get_secure_cookie('REMOTE_SESSION') is None or self.get_secure_cookie('REMOTE_USER') is None:
            self.set_status(401)
            self.finish()
        else:
            self.set_id()
            self.channels = ["user.%s" % self.get_secure_cookie('REMOTE_USER').decode('ascii')]
            self.on_open()

    def on_open(self, *args, **kwargs):
        """ Invoked for a new connection opened. """
        cls = self.__class__

        self.log.info('Incoming connection %s to channels "%s"' % (self.connection_id, ', '.join(self.channels)))
        cls._connections[self.connection_id] = self
        # send something to the client to let it know that the connection has been established
        self.on_message("ping")

        # Bind channels
        for channel in self.channels:
            if channel not in cls._channels:
                cls._channels[channel] = {}

            cls._channels[channel][self.connection_id] = self.get_secure_cookie('REMOTE_SESSION').decode('ascii')

        event_id = self.request.headers.get('Last-Event-ID', None)
        if event_id:
            self.log.debug('Client %s last event ID: %s' % (self.connection_id, event_id))
            i = 0
            for i, msg in enumerate(cls._cache):
                if msg['id'] == event_id:
                    break

            for msg in cls._cache[i+1:]:
                if msg['channel'] == 'broadcast' or msg['channel'] in self.channels:
                    self.on_message(msg['body'])

    def on_close(self):
        """ Invoked when the connection for this instance is closed. """
        cls = self.__class__

        if self.connection_id in cls._connections:
            self.log.info('Connection %s is closed' % self.connection_id)
            del cls._connections[self.connection_id]

        for channel in self.channels:
            if channel in cls._channels:
                if len(cls._channels[channel]) > 1:
                    del cls._channels[channel][self.connection_id]
                else:
                    del cls._channels[channel]

    def on_connection_close(self):
        """ Closes the connection for this instance """
        self.on_close()
        self.stream.close()

    @classmethod
    def notify(cls, xml, channel='broadcast'):
        eventType = stripNs(xml.xpath('/g:Event/*', namespaces={'g': "http://www.gonicus.de/Events"})[0].tag)
        func = getattr(cls, "_handle" + eventType)
        func(xml, channel)

    @classmethod
    def _handleObjectChanged(cls, data, channel):
        data = data.ObjectChanged

        SseHandler.send_message({
            "uuid": data.UUID.text if hasattr(data, "UUID") else "",
            "dn": data.DN.text if hasattr(data, "DN") else "",
            "lastChanged": data.ModificationTime.text,
            "changeType": data.ChangeType.text,
        }, topic="objectChange", channel=channel)

    @classmethod
    def _handleNotification(cls, data, channel):
        data = data.Notification

        title = N_("System notification")
        icon = "dialog-information"
        timeout = 10000
        if hasattr(data, 'Title'):
            title = data.Title.text
        if hasattr(data, 'Icon'):
            icon = data.Icon.text
        if hasattr(data, 'Timeout'):
            timeout = int(data.Timeout.text)

        SseHandler.send_message({
            "title": title,
            "body": data.Body.text,
            "icon": icon, "timeout": timeout}, topic="notification", channel=channel)

    @classmethod
    def _handleObjectCloseAnnouncement(cls, data, channel):
        data = data.ObjectCloseAnnouncement

        minutes = data.Minutes.text if hasattr(data, "Minutes") else ""

        SseHandler.send_message({
            "uuid": data.UUID.text,
            "minutes": minutes,
            "state": data.State.text}, topic="objectCloseAnnouncement", channel=channel, session_id=data.SessionId.text)


    @classmethod
    def send_message(cls, msg, topic=None, channel='broadcast', session_id=None):
        """ Sends a message to all live connections """
        id = str(uuid.uuid4())

        if isinstance(msg, dict):
            msg = dumps(msg)

        dataString = format("%s\n" % "\n".join([("data: %s" % x) for x in msg.splitlines() if not x == '']))

        if topic is not None:
            message = format('id: %s\nevent: %s\n%s\n' % (id, topic, dataString))
        else:
            message = format('id: %s\n%s\n' % (id, dataString))

        cls._cache.append({
            'id': id,
            'channel': channel,
            'body': message,
        })
        if len(cls._cache) > cls._cache_size:
            cls._cache = cls._cache[-cls._cache_size:]

        if channel == 'broadcast':
            clients = []
            for chan in cls._channels:
                for client in cls._channels[chan]:
                    clients.append(client)
        elif session_id is not None:
            clients = []
            channel_clients = cls._channels.get(channel, [])
            for connection_id in channel_clients:
                if channel_clients[connection_id] == session_id:
                    clients.append(connection_id)
        else:
            clients = cls._channels.get(channel, [])

        logging.info('Sending %s "%s" in channel %s (session: %s) to %s clients' % (topic, msg, channel, session_id, len(clients)))
        for client_id in clients:
            client = cls._connections[client_id]
            client.on_message(message)

    def on_message(self, message):
        self.write(message)
        self.flush()
