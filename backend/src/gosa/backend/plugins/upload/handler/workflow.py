# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import logging
import os
from zipfile import ZipFile
from lxml import objectify, etree
from pkg_resources import resource_filename
from gosa.backend.plugins.upload.main import IUploadFileHandler
from gosa.backend.components.workflowregistry import WorkflowRegistry
from gosa.common import Environment


class WorkflowUploadHandler(IUploadFileHandler):

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing workflow upload handler")

    def handle_upload(self, file):
        self.log.debug("uploaded workflow file received %s" % file.name)
        self.extract(file.name)
        
    def extract(self, fn):
        with ZipFile(fn) as workflow_zip:
            if workflow_zip.testzip():
                self.log.error("bad workflow zip uploaded")
                return
    
            env = Environment.getInstance()
            schema = etree.XMLSchema(file=resource_filename("gosa.backend", "data/workflow.xsd"))
            parser = objectify.makeparser(schema=schema)
    
            try:
                with workflow_zip.open('workflow.xml') as dsc:
                    root = objectify.fromstring(dsc.read(), parser)
                    id = objectify.ObjectPath("Workflow.Id")(root)[0].text
    
                    target = os.path.join(env.config.get("core.workflow_path", "/var/lib/gosa/workflows"), id)
                    workflow_zip.extractall(target)

                    WorkflowRegistry.get_instance().refresh()
    
            except KeyError:
                self.log.error("bad workflow zip uploaded - no workflow.xml present")
