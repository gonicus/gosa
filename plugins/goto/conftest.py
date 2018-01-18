import pytest
from gosa.common import Environment
from gosa.common.components import PluginRegistry, ObjectRegistry
import os


def pytest_unconfigure(config):
    PluginRegistry.getInstance('HTTPService').srv.stop()
    PluginRegistry.shutdown()


@pytest.fixture(scope="session", autouse=True)
def use_test_config():
    Environment.reset()
    if pytest.config.getoption("--travis"):
        Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "configs", "travis_conf")
    else:
        Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "configs", "test_conf")
    Environment.noargs = True

    oreg = ObjectRegistry.getInstance()  # @UnusedVariable
    pr = PluginRegistry()  # @UnusedVariable
    cr = PluginRegistry.getInstance("CommandRegistry") # @UnusedVariable
