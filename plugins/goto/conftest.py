import pytest
import psutil
from gosa.common import Environment
from gosa.common.components import PluginRegistry, ObjectRegistry
import os

# def pytest_addoption(parser):
#     parser.addoption("--runslow", action="store_true",
#                      help="run slow tests")


def pytest_unconfigure(config):
    PluginRegistry.getInstance('HTTPService').srv.stop()
    PluginRegistry.shutdown()

@pytest.fixture(scope="session", autouse=True)
def use_test_config():
    Environment.reset()
    travis = False
    for pid in psutil.pids():
        environ = psutil.Process(pid).environ()
        if 'TRAVIS' in environ:
            travis = True
            break

    if travis:
        Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "travis_conf")
    else:
        Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "test_conf")
    Environment.noargs = True

    oreg = ObjectRegistry.getInstance()  # @UnusedVariable
    pr = PluginRegistry()  # @UnusedVariable
    cr = PluginRegistry.getInstance("CommandRegistry") # @UnusedVariable
