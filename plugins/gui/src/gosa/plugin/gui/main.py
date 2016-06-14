import pkg_resources
import os
import tornado.web

class GuiPlugin(tornado.web.StaticFileHandler):

    def initialize(self, path):
        # Ignore 'path'.
        print(os.path.join(os.getcwd(), 'plugins', 'gui', 'frontend', 'gosa', 'build'))
        super(GuiPlugin, self).initialize(os.path.join(os.getcwd(), 'plugins', 'gui', 'frontend', 'gosa', 'build'))