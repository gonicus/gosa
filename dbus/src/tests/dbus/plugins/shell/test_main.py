# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import os
import shutil
import pytest
import time
from unittest import TestCase, mock

from gosa.common import Environment
from gosa.dbus.plugins.shell.main import DBusShellHandler, NoSuchScriptException


class DBusShellHandlerTestCase(TestCase):

    def setUp(self):
        super(DBusShellHandlerTestCase, self).setUp()
        self.env = Environment.getInstance()
        self.path = self.env.config.get("dbus.script-path")
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        with mock.patch("gosa.dbus.plugins.shell.main.dbus.Interface") as m_if:
            self.handler = DBusShellHandler()
            self.m_systemd = m_if.return_value

        # add test script to path
        for root, dirs, files in os.walk(os.path.join(os.path.dirname(__file__), "shelld")):
            for script in files:
                shutil.copyfile(os.path.join(root, script), os.path.join(self.path, script))
                if script != "noexec.sh":
                    shutil.copymode(os.path.join(root, script), os.path.join(self.path, script))
        if not os.path.exists(os.path.join(os.path.dirname(__file__), "shelld", "test_dir")):
            os.makedirs(os.path.join(os.path.dirname(__file__), "shelld", "test_dir"))
        time.sleep(0.2)

    def tearDown(self):
        super(DBusShellHandlerTestCase, self).tearDown()
        self.handler.remove_from_connection()
        del self.handler
        shutil.rmtree(os.path.join(self.path))

    def test_shell_list(self):
        assert "ls" in self.handler.shell_list()
        os.remove(os.path.join(self.path, "ls.sh"))
        time.sleep(0.2)
        assert "ls" not in self.handler.shell_list()

    def test_shell_exec(self):

        with pytest.raises(NoSuchScriptException):
            self.handler.shell_exec("unknown_script", [])

        res = self.handler.shell_exec("ls", ["--directory", "/tmp/shell.d/"])
        lines = res['stdout'].split("\n")
        assert res['code'] == 0
        assert res['stderr'] == ''
        assert "ls.sh" in lines