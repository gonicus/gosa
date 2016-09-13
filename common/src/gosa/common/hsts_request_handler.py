# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from tornado.web import RequestHandler, StaticFileHandler


class HSTSRequestHandler(RequestHandler):

    def data_received(self, chunk):  # pragma: nocover
        pass

    def __init__(self, application, request, hsts=True,
                 **kwargs):
        super(HSTSRequestHandler, self).__init__(application, request, **kwargs)
        self.hsts = hsts

    def finish(self, chunk=None):
        if self.hsts is True:
            self.set_header("Strict-Transport-Security", "max-age=31536000")

        super(HSTSRequestHandler, self).finish(chunk)


class HSTSStaticFileHandler(StaticFileHandler):

    def data_received(self, chunk):  # pragma: nocover
        pass

    def __init__(self, application, request, hsts=True,
                 **kwargs):
        super(HSTSStaticFileHandler, self).__init__(application, request, **kwargs)
        self.hsts = hsts

    def finish(self, chunk=None):
        if self.hsts is True:
            self.set_header("Strict-Transport-Security", "max-age=31536000")

        super(HSTSStaticFileHandler, self).finish(chunk)
