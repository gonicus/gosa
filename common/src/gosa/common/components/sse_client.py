# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import logging
from threading import Thread
from tornado import httpclient, httputil
from tornado.ioloop import IOLoop
from gosa.common.gjson import loads
from json import JSONDecodeError

APPLICATION_JSON = 'application/json'

DEFAULT_CONNECT_TIMEOUT = 60

class Event(object):
    def __init__(self):
        self.name = None
        self.data = None
        self.id = None

    def __repr__(self):
        return "Event\n  id: %s\n  name: %s\n  data:\n\t%s" % (str(self.id), str(self.name), "\n\t".join(self.data.splitlines()))

class BaseSseClient():
    """"
    Base class for server sent event clients.
    """

    def __init__(self, connect_timeout=DEFAULT_CONNECT_TIMEOUT):
        self.log = logging.getLogger(__name__)
        self.connect_timeout = connect_timeout
        httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
        self.client = httpclient.AsyncHTTPClient()

    def connect(self, url):
        """Connect to the server.
        :param str url: server URL.
        """

        # disconnect old session if there is one
        if hasattr(self, "connection"):
            del self.connection

        request = httpclient.HTTPRequest(url=url,
                                         method='GET',
                                         request_timeout=0,
                                         connect_timeout=self.connect_timeout,
                                         streaming_callback=self.parse_event)
        self.connection = self.client.fetch(request, self.handle_request)
        self.thread = Thread(target=self.start)
        self.thread.start()

        return self.connection

    def start(self):
        IOLoop.instance().start()

    def handle_request(self, response):
        if response.error:
            self.log.error("Error: %s" % response.error)
        else:
            self.log.debug(response.body)
        IOLoop.instance().stop()

    def close(self):
        """
        Close connection.
        """

        if not hasattr(self, "connection"):
            raise RuntimeError('SSE connection is already closed.')
        del self.connection

    def parse_event(self, rawEvent):
        """
        Parse the SSE event and call the on_event method with the created event dict
        :param str rawEvent: the raw string retrieved from the SSE server
        """
        event = Event()
        for line in rawEvent.strip().splitlines():
            (field, value) = line.decode().split(":", 1)
            field = field.strip()
            if field == "data":
                try:
                    data = loads(value.strip())
                except JSONDecodeError as e:
                    # no json just use string
                    data = value.strip()
                if event.data is None:
                    event.data = data
                else:
                    event.data = "%s\n%s" % (event.data, data)
            elif field == "id":
                event.id = value.strip()
            elif field == "event":
                event.name = value.strip()
        self.on_event(event)

    def on_event(self, event):
        raise NotImplementedError()
