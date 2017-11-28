import pytest
from gosa.common import Environment
from gosa.common.components import PluginRegistry
import os
try:
    from gosa.common.components.dbus_runner import DBusRunner
    has_dbus = True
except ImportError:
    has_dbus = False


@pytest.fixture(scope="session", autouse=True)
def use_test_config(request):
    Environment.reset()
    if os.environ.get("TRAVIS_BRANCH") is not None:
        Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "travis_conf")
    else:
        Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "test_conf")
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
