# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.backend.routes.sse.main import SseHandler
from gosa.common.gjson import loads
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.web import Application

class SseHandlerTestCase(AsyncHTTPTestCase):

    def get_app(self):
        return Application([('/events', SseHandler)])

    def handleMessage(self, msg):
        for line in msg.strip().splitlines():
            (field, value) = line.decode().split(":")
            field = field.strip()
            if field == "data":
                data = value.strip()
                assert data == "Test"

        self.stop()

    def test_subscribe(self):
        self.http_client.fetch(self.get_url('/events'), streaming_callback = self.handleMessage, headers={"content-type":"text/event-stream"})
        # post something
        self.http_client.fetch(self.get_url('/events'), method="POST", body="Test")
        self.wait()
