# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import os
import shutil
from gosa.common import Environment
from gosa.common.error import GosaErrorHandler as C
from gosa.common.components import Plugin, PluginRegistry
from gosa.common.components.command import Command
from gosa.common.utils import N_
from gosa.backend.components.workflow import Workflow, WorkflowException
from lxml import objectify, etree
from pkg_resources import resource_filename

# Register the errors handled  by us
C.register_codes(dict(
    WORKFLOW_DIR_ERROR=N_("Workflow directory '%(path)s' does not exist"),
    WORKFLOW_PERMISSION_DELETE=N_("No permission to delete workflow '%(id)s'"),
    WORKFLOW_DELETE_ERROR=N_("Error removing workflow '%(id)s': %(error)s")
))


"""
Workflow Registery
==================

TODO: documentation
"""
class WorkflowRegistry(Plugin):
    _target_ = "workflow"
    instance = None
    env = None
    __acl_resolver = None

    @staticmethod
    def get_instance():
        if not WorkflowRegistry.instance:
            WorkflowRegistry.instance = WorkflowRegistry()
        return WorkflowRegistry.instance

    def __init__(self):
        self.env = Environment.getInstance()
        self.__acl_resolver = PluginRegistry.getInstance("ACLResolver")
        self.__path = self.env.config.get("core.workflow_path", "/var/lib/gosa/workflows")

        if not os.path.exists(self.__path) or not os.path.isdir(self.__path):
            raise WorkflowException(C.make_error('WORKFLOW_DIR_ERROR', path=self.__path))

        if WorkflowRegistry.instance is None:
            WorkflowRegistry.instance = self
            self._update_map()
        else:
            raise Exception("This is a singleton, please use getInstance instead")

    @Command(needsUser=True, __help__=N_("List available workflows"))
    def getWorkflows(self, user):
        """
        Returns a list of the names of all workflows that are found by the registry in the file system or that are
        added via the 'add' method.
        """

        res = {}
        for id, workflow in self._workflows.items():
            topic = "%s.workflows.%s" % (self.env.domain, id)
            if self.__acl_resolver.check(user, topic, "r", base=self.env.base):
                res[id] = dict(
                    name=workflow["display_name"],
                    description=workflow["description"],
                    icon=workflow["icon"]
                )

        return res

    @Command(needsUser=True, __help__=N_("Add a new workflow to the list of available workflows"))
    def removeWorkflow(self, user, id):
        topic = "%s.workflows.%s" % (self.env.domain, id)
        if self.__acl_resolver.check(user, topic, "d", base=self.env.base):
            try:
                shutil.rmtree(os.path.join(self.__path, id))
            except OSError as e:
                raise WorkflowException(C.make_error('WORKFLOW_DELETE_ERROR', id=id, error=str(e)))

            self._update_map()
        else:
            raise WorkflowException(C.make_error('WORKFLOW_PERMISSION_DELETE', id=id))

    def get_workflow(self, id):
        """
        Creates a workflow object with the given id or None if that does not exist.
        """
        #TODO: needs to be done like openObject()
        if id in self._workflows:
            return Workflow(self._workflows[id]["file_path"])

    def __add(self, wf_path):
        """
        Read workflow from the given path and add it so the registry.
        """
        schema = etree.XMLSchema(file=resource_filename("gosa.backend", "data/workflow.xsd"))
        parser = objectify.makeparser(schema=schema)
        root = objectify.parse(os.path.join(wf_path, "workflow.xml"), parser).getroot()

        description = None
        try:
            description = objectify.ObjectPath("Workflow.Description")(root)[0].text
        except:
            pass

        icon = None
        try:
            icon = objectify.ObjectPath("Workflow.Icon")(root)[0].text
        except:
            pass

        id = objectify.ObjectPath("Workflow.Id")(root)[0].text
        entry = dict(
          id=id,
          file_path=wf_path,
          display_name=objectify.ObjectPath("Workflow.DisplayName")(root)[0].text,
          description=description,
          icon=icon
        )

        self._workflows[id] = entry

    def _update_map(self):
        """
        Recreates the internal workflow map.
        """
        self._workflows = {}
        for fn in os.listdir(self.__path):
            self.__add(os.path.join(self.__path, fn))
