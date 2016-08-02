import pytest
from gosa.common import Environment
from gosa.common.components import PluginRegistry, ObjectRegistry
import os

@pytest.fixture(scope="session", autouse=True)
def use_test_config():
    Environment.reset()
    Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "test_conf")
    Environment.noargs = True

    PluginRegistry(component='gosa.client.module')  # @UnusedVariable
