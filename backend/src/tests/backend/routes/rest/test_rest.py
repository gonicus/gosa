# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import base64
from gosa.backend.routes.rest.main import RestApi
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

app = Application([('/api/(.*)', RestApi)])

class RestApiTestCase(AsyncHTTPTestCase):

    def get_app(self):
        return app

    def open_with_auth(self, url, method, username, password):
        cred = base64.b64encode(bytes(username + ":" + password, "utf-8")).decode("ascii")
        return self.fetch(url,
            method=method,
            headers={
                'Authorization': 'Basic %s' % cred
            }
        )

    def test_getUnknown(self):
        response = self.open_with_auth('/api/foo/bar', 'GET', 'admin', 'secret')
        assert response.code == 404

    def test_getExisting(self):
        # without credentials this must be forbidden
        rv = self.fetch('/api/Testabteilung1/user/sepp')
        assert rv.code == 401

        rv = self.open_with_auth('/api/Testabteilung1/user/sepp', 'GET', 'admin', 'secret')
        assert rv.code == 200
        assert b'"customAttr": "foobar"' in rv.body

        rv = self.open_with_auth('/api/Testabteilung1/user/sepp/', 'GET', 'admin', 'secret')
        assert rv.code == 200
        assert b'"customAttr": "foobar"' in rv.body
