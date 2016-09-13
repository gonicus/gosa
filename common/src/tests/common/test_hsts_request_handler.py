# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details
from gosa.common import Environment
from gosa.common.hsts_request_handler import HSTSRequestHandler, HSTSStaticFileHandler
from tests.RemoteTestCase import RemoteTestCase
from tornado.web import Application


class ImageHandler(HSTSStaticFileHandler):

    def initialize(self):
        env = Environment.getInstance()
        path = env.config.get("user.image-path", "/var/lib/gosa/images")
        super(ImageHandler, self).initialize(path)


class HstsRequestHandlerTestCase(RemoteTestCase):

    def get_app(self):
        return Application([
            ('/hsts', HSTSRequestHandler, {'hsts': True}),
            ('/nohsts', HSTSRequestHandler, {'hsts': False}),
            ('/static/hsts', ImageHandler, {'hsts': True}),
            ('/static/nohsts', ImageHandler, {'hsts': False})
        ])

    def test_hsts(self):
        response = self.fetch("/hsts")
        assert 'Strict-Transport-Security' in response.headers

        response = self.fetch("/nohsts")
        assert 'Strict-Transport-Security' not in response.headers

        response = self.fetch("/static/hsts")
        print(response)
        assert 'Strict-Transport-Security' in response.headers

        response = self.fetch("/static/nohsts")
        assert 'Strict-Transport-Security' not in response.headers