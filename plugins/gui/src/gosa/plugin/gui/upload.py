import os
import logging
from zipfile import ZipFile
from gosa.backend.plugins.upload.main import IUploadFileHandler
from gosa.common import Environment
from gosa.plugin.gui import frontend_path


class WidgetUploadHandler(IUploadFileHandler):

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing dashboard widget upload handler")

    def handle_upload(self, file, request):
        filename = request.headers.get('X-File-Name')
        self.log.debug("uploaded widget package received %s" % filename)
        self.extract(file.f_out.name, filename)
        file.release()

    def extract(self, fn, real_name):
        try:

            with ZipFile(fn, 'r') as widget_zip:

                if widget_zip.testzip():
                    self.log.error("bad widget zip uploaded")
                    return
                # extract filename from zip
                widget_zip.extractall(os.path.join(frontend_path, "gosa", "uploads", "widgets"))

        except Exception as e:
            print(e)
            raise e
