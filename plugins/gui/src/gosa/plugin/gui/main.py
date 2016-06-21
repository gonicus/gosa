import os
import tornado.web

class GuiPlugin(tornado.web.StaticFileHandler):

    def initialize(self):
        super(GuiPlugin, self).initialize(path=os.path.join(os.getcwd(), 'plugins', 'gui', 'frontend', 'gosa', 'build'))

    def get(self, path, include_body=True):
        if not path:
            path = "index.html"
        super(GuiPlugin, self).get(path, include_body)