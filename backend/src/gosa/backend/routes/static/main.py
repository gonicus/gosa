import tornado.web
import pkg_resources


class StaticHandler(tornado.web.StaticFileHandler):

    def initialize(self):
        path = pkg_resources.resource_filename("gosa.backend", "data/templates")
        super(StaticHandler, self).initialize(path)
