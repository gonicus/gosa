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
from gosa.backend.objects import ObjectFactory


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", help="run slow tests")


def pytest_configure(config):
    sys._called_from_test = True


def pytest_unconfigure(config):
    del sys._called_from_test
    PluginRegistry.getInstance('HTTPService').srv.stop()
    shutdown()


@pytest.fixture(scope="session", autouse=True)
def use_test_config():
    Environment.reset()
    Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "configs", "test_conf")
    Environment.noargs = True

    # clear json-backend
    with open(Environment.getInstance().config.get("backend-json.database-file"), 'w') as f:
        f.write('{}')

    Environment.getInstance()
    if not sys.stdout.encoding:
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    if not sys.stderr.encoding:
        sys.stderr = codecs.getwriter('utf8')(sys.stderr)

    pkg_resources.require('gosa.common==%s' % VERSION)
    main()
    # sync index
    index = PluginRegistry.getInstance("ObjectIndex")
    index.syncIndex()

    # create all classes to prevent test timeouts
    ObjectFactory.getInstance().create_classes()
