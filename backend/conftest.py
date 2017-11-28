# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import pytest
from gosa.backend.main import *

def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true",
                     help="run slow tests")
    parser.addoption("--travis", action="store_true", default=False, help="Use travis config for tests")


def pytest_configure(config):
    sys._called_from_test = True


def pytest_unconfigure(config):
    del sys._called_from_test
    PluginRegistry.getInstance('HTTPService').srv.stop()
    shutdown()

@pytest.fixture(scope="session", autouse=True)
def use_test_config():
    Environment.reset()
    if pytest.config.getoption("--travis"):
        Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "travis_conf")
    else:
        Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "test_conf")
    Environment.noargs = True

    env = Environment.getInstance()
    workflow_path = env.config.get("core.workflow_path", "/var/lib/gosa/workflows")

    # create workflow path
    if not os.path.exists(workflow_path):
        os.makedirs(workflow_path)

    main()
