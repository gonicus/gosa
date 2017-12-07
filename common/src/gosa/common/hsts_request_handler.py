# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from tornado.stack_context import StackContext
from tornado.web import RequestHandler, StaticFileHandler

from gosa.common import Environment
from gosa.common.env import SessionMixin, SessionContext


class HSTSRequestHandler(RequestHandler, SessionMixin):

    def data_received(self, chunk):  # pragma: nocover
        pass

    def __init__(self, application, request, hsts=True,
                 **kwargs):
        super(HSTSRequestHandler, self).__init__(application, request, **kwargs)
        self.hsts = hsts
        self.env = Environment.getInstance()

    def prepare(self):
        if self.request.protocol == "http" and self.env.config.getboolean("http.ssl") is True:
            self.redirect("https://%s" % self.request.full_url()[len("http://"):], permanent=True)

    def _execute(self, transforms, *args, **kwargs):
        with self.make_session(skip_context_check=True) as session:
            with StackContext(SessionContext(session)):
                super(HSTSRequestHandler, self)._execute(transforms, *args, **kwargs)

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
        self.env = Environment.getInstance()

    def prepare(self):
        if self.request.protocol == "http" and self.env.config.getboolean("http.ssl") is True:
            self.redirect("https://%s" % self.request.full_url()[len("http://"):], permanent=True)

    def finish(self, chunk=None):
        if self.hsts is True:
            self.set_header("Strict-Transport-Security", "max-age=31536000")

        super(HSTSStaticFileHandler, self).finish(chunk)
