# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
import base64
from gosa.backend.plugin.rest.main import RestApi
from flask import Flask

class RestApiTestCase(unittest.TestCase):

    def setUp(self):
        app = Flask(__name__)
        app.testing = True

        flask_view = RestApi.as_view("test_rest_api")
        app.add_url_rule("/api/<path:path>", view_func=flask_view)
        self.client = app.test_client()

    def open_with_auth(self, url, method, username, password):
        cred = base64.b64encode(bytes(username + ":" + password, "utf-8")).decode("ascii")
        return self.client.open(url,
            method=method,
            headers={
                'Authorization': 'Basic %s' % cred
            }
        )

    def test_getUnknown(self):
        rv = self.open_with_auth('/api/foo/bar', 'GET', 'admin', 'secret')
        assert rv.status_code == 404

    def test_getExisting(self):
        # without credentials this must be forbidden
        rv = self.client.get('/api/Testabteilung1/user/sepp')
        assert rv.status_code == 401

        rv = self.open_with_auth('/api/Testabteilung1/user/sepp', 'GET', 'admin', 'secret')
        assert rv.status_code == 200
        assert b'"customAttr": "foobar"' in rv.data

        rv = self.open_with_auth('/api/Testabteilung1/user/sepp/', 'GET', 'admin', 'secret')
        assert rv.status_code == 200
        assert b'"customAttr": "foobar"' in rv.data
