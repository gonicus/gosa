import os
import logging
from lxml import objectify

from lxml import etree
from zipfile import ZipFile
from gosa.backend.plugins.upload.main import IUploadFileHandler
from gosa.backend.routes.sse.main import SseHandler
from gosa.common import Environment
from gosa.common.event import EventMaker

frontend_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', '..', 'frontend'))


class WidgetUploadHandler(IUploadFileHandler):

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing dashboard widget upload handler")

    def handle_upload(self, file, request):
        filename = request.headers.get('X-File-Name')
        self.log.debug("uploaded widget package received %s" % filename)
        self.extract(file.f_out.name, filename)

    def extract(self, fn, real_name):
        try:

            with ZipFile(fn, 'r') as widget_zip:

                if widget_zip.testzip():
                    self.log.error("bad widget zip uploaded")
                    return
                # extract filename from zip
#TODO: wrong path, needs to be configurable
                widget_zip.extractall(os.path.join(frontend_path, "gosa", "uploads", "widgets"))
                # send the event to the clients
                e = EventMaker()

                ev = e.Event(e.PluginUpdate(
                    e.Namespace(real_name.split(".")[0])
                ))
                event_object = objectify.fromstring(etree.tostring(ev, pretty_print=True).decode('utf-8'))
                SseHandler.notify(event_object, channel="broadcast")

        except Exception as e:
            print(e)
            raise e
