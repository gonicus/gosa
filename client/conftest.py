import pytest
from gosa.common import Environment
from gosa.common.components import PluginRegistry
import os
from gosa.common.components.dbus_runner import DBusRunner


@pytest.fixture(scope="session", autouse=True)
def use_test_config(request):
    Environment.reset()
    Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "test_conf")
    Environment.noargs = True
    env = Environment.getInstance()

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
        dr.stop()

    request.addfinalizer(shutdown)
