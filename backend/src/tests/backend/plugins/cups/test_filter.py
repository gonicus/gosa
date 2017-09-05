# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import unittest
from shutil import copyfile
from unittest import mock

from gosa.backend.plugins.cups.filter import *


class FilterValidatorTests(unittest.TestCase):

    def test_GetMakeModelFromPPD(self):
        base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")

        filter = GetMakeModelFromPPD(None)
        (key, res) = filter.process(None, "ppd", {
            "ppd": {"value": [os.path.join(base_dir, "test.ppd")]},
            "maker": {"value": ["Epson"]},
            "serverPPD": {"value": ["Some printer"]}
        }, "maker", "serverPPD", "true")

        assert res["maker"]["value"][0] == "Ricoh"
        assert res["serverPPD"]["value"][0] == "openprinting-ppds:0/ppd/openprinting/Ricoh/PS/Ricoh-MP_C2003_PS.ppd"

        # do not override
        (key, res) = filter.process(None, "ppd", {
            "ppd": {"value": [os.path.join(base_dir, "test.ppd")]},
            "maker": {"value": ["Epson"]},
            "serverPPD": {"value": ["Some printer"]}
        }, "maker", "serverPPD")

        assert res["maker"]["value"][0] == "Epson"
        assert res["serverPPD"]["value"][0] == "Some printer"

    def test_DeleteOldFile(self):
        base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")

        copy_file = "/tmp/test.ppd"
        copyfile(os.path.join(base_dir, "test.ppd"), copy_file)

        filter = DeleteOldFile(None)
        base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")

        with mock.patch("gosa.backend.plugins.cups.filter.PluginRegistry.getInstance") as m_reg:
            m_reg.return_value.search.return_value = ["1", "2"]
            data = {
                "ppd": {
                    "orig_value": [copy_file],
                    "value": [os.path.join(base_dir, "test.ppd")]
                }
            }
            filter.process(None, "ppd", data)

            assert os.path.exists(copy_file)

            m_reg.return_value.search.return_value = ["1"]

            filter.process(None, "ppd", data)
            assert not os.path.exists(copy_file)
