# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.backend.plugin.sse.main import SseHandler
from gosa.common.gjson import loads
from flask import Flask

class SseHandlerTestCase(unittest.TestCase):

    def setUp(self):
        app = Flask(__name__)
        app.testing = True

        flask_view = SseHandler.as_view("test_rest_sse")
        app.add_url_rule("/subscribe", view_func=flask_view)
        self.client = app.test_client()

    def test_subscribe(self):
        rv = self.client.get('/subscribe')
        assert rv.mimetype == "text/event-stream"
        assert rv.charset == "utf-8"

        data = yield loads(rv.data.decode('utf-8'))
        assert data == "erfg"
