import pytest
from gosa.common import Environment
from gosa.common.components import PluginRegistry
import os
try:
    from gosa.common.components.dbus_runner import DBusRunner
    has_dbus = True
except ImportError:
    has_dbus = False


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", help="run slow tests")
    parser.addoption("--travis", action="store_true", default=False, help="Use travis config for tests")


@pytest.fixture(scope="session", autouse=True)
def use_test_config(request):
    Environment.reset()
    if pytest.config.getoption("--travis"):
        Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "configs", "travis_conf")
    else:
        Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "configs", "test_conf")
    Environment.noargs = True
    env = Environment.getInstance()

    if has_dbus:
        # Enable DBus runner
        dr = DBusRunner()
        dr.start()

    PluginRegistry(component='gosa.client.module')  # @UnusedVariable
    env.active = True

    def shutdown():
        env.active = False

        # Wait for threads to shut down
        for t in env.threads:
            if hasattr(t, 'stop'):
                t.stop()
            if hasattr(t, 'cancel'):
                t.cancel()
            t.join(2)

        PluginRegistry.shutdown()
        if has_dbus:
            dr.stop()

    request.addfinalizer(shutdown)
