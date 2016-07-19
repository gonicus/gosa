import uuid
import time
import hashlib
import logging
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

        # Bind channels
        for channel in self.channels:
            if channel not in cls._channels:
                cls._channels[channel] = []

            cls._channels[channel].append(self.connection_id)

        event_id = self.request.headers.get('Last-Event-ID', None)
        if event_id:
            self.log.info('Client %s last event ID: %s' % (self.connection_id, event_id))
            i = 0
            for i, msg in enumerate(cls._cache):
                if msg['id'] == event_id: break

            for msg in cls._cache[i:]:
                if msg['channel'] in self.channels:
                    self.on_message(msg['body'])

    def on_close(self):
        """ Invoked when the connection for this instance is closed. """
        cls = self.__class__

        self.log.info('Connection %s is closed' % self.connection_id)
        del cls._connections[self.connection_id]

        for channel in self.channels:
            if len(cls._channels[channel]) > 1:
                cls._channels[channel].remove(self.connection_id)
            else:
                del cls._channels[channel]

    def on_connection_close(self):
        """ Closes the connection for this instance """
        self.on_close()
        self.stream.close()

    @classmethod
    def send_message(cls, msg, topic=None, channel='broadcast'):
        """ Sends a message to all live connections """
        id = str(uuid.uuid4())

        dataString = format("%s\n" % "\n".join([("data: %s" % x) for x in msg.splitlines() if not x == '']))

        if (topic != None):
            message = format('id: %s\nevent: %s\n%s' % (id, topic, dataString))
        else:
            message = format('id: %s\n%s' % (id, dataString))

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
        else:
            clients = cls._channels.get(channel, [])

        logging.info('Sending %s "%s" to channel %s for %s clients' % (topic, msg, channel, len(clients)))
        for client_id in clients:
            client = cls._connections[client_id]
            client.on_message(message)

    def on_message(self, message):
        self.write(message)
        self.flush()
