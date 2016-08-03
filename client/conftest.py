import pytest
from gosa.common import Environment
from gosa.common.components import PluginRegistry
import os
from gosa.common.components.dbus_runner import DBusRunner


def pytest_unconfigure(config):
    global dr
    Environment.getInstance().active = False
    PluginRegistry.shutdown()
    dr.stop()

@pytest.fixture(scope="session", autouse=True)
def use_test_config():
    global dr
    Environment.reset()
    Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "test_conf")
    Environment.noargs = True
    env = Environment.getInstance()

    # Enable DBus runner
    dr = DBusRunner()
    dr.start()

    PluginRegistry(component='gosa.client.module')  # @UnusedVariable
    env.active = True
