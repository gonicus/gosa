# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application
from gosa.backend.routes.sse.main import SseHandler

class SseHandlerTestCase(AsyncHTTPTestCase):

    def get_app(self):
        return Application([('/events', SseHandler)])

    def handleMessage(self, msg):
        for line in msg.strip().splitlines():
            (field, value) = line.decode().split(":")
            field = field.strip()
            if field == "data":
                self.last_data = value.strip()
                assert self.last_data == self.check_data
            if field == "id":
                self.last_id = value.strip()
            if field == "event":
                self.last_event = value.strip()
                assert self.last_event == self.check_event

        self.stop()

    def test_subscribe(self):
        self.http_client.fetch(self.get_url('/events'), self.stop, streaming_callback=self.handleMessage)
        # post something
        self.check_data = "Test"
        self.http_client.fetch(self.get_url('/events'), self.stop, method="POST", body=self.check_data)
        self.wait()

    def test_missed_events(self):
        # initial connection
        future = self.http_client.fetch(self.get_url('/events'), self.stop, streaming_callback=self.handleMessage)
        self.check_data = "Test"
        self.http_client.fetch(self.get_url('/events'), self.stop, method="POST", body=self.check_data)
        self.wait()
        del future

        self.check_data = "Deferred Test"
        self.http_client.fetch(self.get_url('/events'), self.stop, method="POST", body=self.check_data)
        self.wait()

        self.http_client.fetch(self.get_url('/events'), self.stop,
                               headers={'Last-Event-ID': self.last_id})
        self.wait()

    def test_named_events(self):
        self.http_client.fetch(self.get_url('/events'), self.stop, streaming_callback=self.handleMessage)

        self.check_data = "Test"
        self.check_event = "txt"
        self.http_client.fetch(self.get_url('/events?event=txt'), self.stop, method="POST", body=self.check_data)
        self.wait()