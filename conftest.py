import pytest
import sys
from gosa.common import Environment
import os


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", help="run slow tests")
    parser.addoption("--travis", action="store_true", default=False, help="Use travis config for tests")


def pytest_configure(config):
    sys._called_from_test = True


def pytest_unconfigure(config):
    del sys._called_from_test


@pytest.fixture(scope="session", autouse=True)
def use_test_config():
    Environment.reset()
    Environment.reset()
    if pytest.config.getoption("--travis"):
        Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "travis_conf")
    else:
        Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "test_conf")
    Environment.noargs = True

