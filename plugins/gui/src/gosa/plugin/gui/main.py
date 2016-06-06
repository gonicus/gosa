import pkg_resources
from flask import Response
from flask.views import MethodView

class GuiPlugin(MethodView):

    def __init__(self):
        print("Heureka!")
        print(pkg_resources.resource_filename('gosa.plugin.gui', 'frontend/build'))

    def get(self):
        print("Serve static file")
        return Response("", mimetype="text/html")