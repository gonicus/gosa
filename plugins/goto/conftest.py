import pytest
from gosa.common import Environment
from gosa.common.components import PluginRegistry, ObjectRegistry
import os


def pytest_unconfigure(config):
    PluginRegistry.getInstance('HTTPService').srv.stop()
    PluginRegistry.shutdown()


@pytest.fixture(scope="session", autouse=True)
def use_test_config():
    oreg = ObjectRegistry.getInstance()  # @UnusedVariable
    pr = PluginRegistry()  # @UnusedVariable
    cr = PluginRegistry.getInstance("CommandRegistry") # @UnusedVariable
