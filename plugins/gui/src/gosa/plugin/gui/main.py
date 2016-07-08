import os
import tornado.web


class GuiPlugin(tornado.web.StaticFileHandler):

    def initialize(self):
        super(GuiPlugin, self).initialize(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                       '..', '..', '..', '..', 'frontend', 'gosa', 'build'),
                                          "index.html")
