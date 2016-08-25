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
from gosa.backend.routes.static.main import *
import os


class StaticHandlerTestCase(AsyncHTTPTestCase):

    def get_app(self):
        return Application([('/static/(?P<path>.*)?', StaticHandler), ('/images/(?P<path>.*)?', ImageHandler)])

    def test_get(self):
        response = self.fetch("/static/default/user.ui")
        assert response.code == 200

        path = Environment.getInstance().config.get("user.image-path", "/tmp/images")
        test_file_name = "test.txt"
        test_path = os.path.join(path, test_file_name)
        if not os.path.exists(test_path):
            with open(test_path, "w") as f:
               f.write("test")

        response = self.fetch("/images/%s" % test_file_name)
        assert response.code == 200
        os.remove(test_path)
