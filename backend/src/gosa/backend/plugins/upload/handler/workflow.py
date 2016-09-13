# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import logging
from gosa.backend.plugins.upload.main import IUploadFileHandler
from gosa.common import Environment


class WorkflowUploadHandler(IUploadFileHandler):

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing workflow upload handler")

    def handle_upload(self, file):
        # TODO: do something with the file

        self.log.debug("uploaded file received %s" % file.name)