# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import pytest
import os
import shutil
from unittest import TestCase, mock
from gosa.backend.components.workflowregistry import *


class WorkflowRegistryTestCase(TestCase):

    def setUp(self):
        super(WorkflowRegistryTestCase, self).setUp()
        # cleanup workflows from other tests
        path = Environment.getInstance().config.get("core.workflow-path", "/tmp/workflows")
        try:
            shutil.rmtree(path)
            os.mkdir(path)
        except:
            pass
        self.reg = WorkflowRegistry.get_instance()
        self.reg.refreshWorkflows()

    def test_singleton(self):
        with pytest.raises(Exception):
            WorkflowRegistry()

    def test_getWorkflows(self):
        assert self.reg.getWorkflows('admin') == {}
        # TODO add tests with some workflows

    def test_removeWorkflow(self):
        with mock.patch("gosa.backend.components.workflowregistry.PluginRegistry.getInstance") as m_acl,\
                pytest.raises(WorkflowException):
            m_acl.return_value.check.return_value = False
            self.reg.removeWorkflow('admin', 'id')
        # TODO add tests with some workflows

    def test_get_workflow(self):
        assert self.reg.get_workflow('id') is None
        # TODO add tests with some workflows

