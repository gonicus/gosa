# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from shutil import copyfile
from unittest import mock

import pytest
import cups

from tests.GosaTestCase import GosaTestCase
from gosa.backend.plugins.cups.main import *


class CupsTestCase(GosaTestCase):
    cups = None
    m_cups = None

    def setUp(self):
        logging.getLogger("gosa.backend.plugins.cups").setLevel(logging.DEBUG)
        self.base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
        super(CupsTestCase, self).setUp()
        with mock.patch("gosa.backend.plugins.cups.main.cups") as m_cups:
            self.cups = CupsClient()
            self.cups.serve()
            m_cups.PPD.side_effect = cups.PPD
            self.m_cups = m_cups

    def tearDown(self):
        logging.getLogger("gosa.backend.plugins.cups").setLevel(logging.INFO)
        super(CupsTestCase, self).tearDown()

    def test_get_printer_list(self):
        self.cups.client.getPPDs.return_value = {
            'gutenprint.5.2://escp2-tx110/expert': {
                'ppd-natural-language': 'en',
                'ppd-model-number': 0,
                'ppd-psversion': '',
                'ppd-make': 'Epson',
                'ppd-type': 'postscript',
                'ppd-device-id': '',
                'ppd-make-and-model': 'Epson Stylus TX110 - CUPS+Gutenprint v5.2.11',
                'ppd-product': ''
            },
            'openprinting-ppds:0/ppd/openprinting/Sharp/Sharp-MX-3116N-ps.ppd': {
                'ppd-natural-language': 'en',
                'ppd-model-number': 0,
                'ppd-psversion': '',
                'ppd-make': 'Sharp',
                'ppd-type': 'postscript',
                'ppd-device-id': 'MFG:Sharp;MDL:Sharp MX-3116N;',
                'ppd-make-and-model': 'Sharp MX-3116N PS, 1.0',
                'ppd-product': ''
            }
        }

        manufacturers = self.cups.getPrinterManufacturers()
        assert len(manufacturers) == 2
        assert "Epson" in manufacturers
        assert "Sharp"in manufacturers

        models = self.cups.getPrinterModels()
        assert len(models) == 0

        models = self.cups.getPrinterModels("Epson")
        assert len(models) == 1
        assert 'gutenprint.5.2://escp2-tx110/expert' in models
        assert models['gutenprint.5.2://escp2-tx110/expert']['value'] == 'Epson Stylus TX110 - CUPS+Gutenprint v5.2.11'

        models = self.cups.getPrinterModels({"maker": "Sharp"})
        assert len(models) == 1
        assert 'openprinting-ppds:0/ppd/openprinting/Sharp/Sharp-MX-3116N-ps.ppd' in models
        assert models['openprinting-ppds:0/ppd/openprinting/Sharp/Sharp-MX-3116N-ps.ppd']['value'] == 'Sharp MX-3116N PS, 1.0'

    def test_getConfigurePrinterTemplate(self):
        self.cups.client.getServerPPD.return_value = os.path.join(self.base_dir, "unknown.ppd")

        with pytest.raises(CupsException):
            self.cups.getConfigurePrinterTemplate("test.ppd")

        # copy test file because it gets deleted after usage
        ppd = os.path.join(self.base_dir, "test.ppd")
        copy_ppd = os.path.join("/tmp", "test.ppd")
        copyfile(ppd, copy_ppd)

        self.cups.client.getServerPPD.return_value = copy_ppd
        template = self.cups.getConfigurePrinterTemplate("test.ppd")

        # 3 tabs
        assert len(template["children"]) == 3
        # lots of constraints
        assert len(template["extensions"]["validator"]["properties"]["constraints"]) == 25

        # general tab must always be the first one
        general = template["children"][0]
        assert general["properties"]["label"] == "General"

    def test_get_attributes_from_ppd(self):
        res = self.cups.get_attributes_from_ppd(os.path.join(self.base_dir, "test.ppd"), ["ModelName", "Manufacturer"])
        assert res["Manufacturer"] == "Ricoh"
        assert res["ModelName"] == "Ricoh MP C2003"
        assert len(res) == 2

    def test_writePPD(self):
        # copy test file because it gets deleted after usage
        ppd = os.path.join(self.base_dir, "test.ppd")
        copy_ppd = os.path.join("/tmp", "test.ppd")
        if not os.path.exists(copy_ppd):
            copyfile(ppd, copy_ppd)
        self.cups.client.getServerPPD.return_value = copy_ppd
        self.cups.client.getServerPPD.side_effect = PPDException("fake exception")
        with pytest.raises(PPDException):
            self.cups.writePPD(None, None, None, None)
        self.cups.client.getServerPPD.side_effect = None

        res = self.cups.writePPD(None, "test.ppd", None, {"PageSize": "A4"})
        assert "gotoPrinterPPD" in res

        # open the newly written PPD and check if the value has been set
        path = get_local_ppd_path(res["gotoPrinterPPD"][0])
        ppd = cups.PPD(path)
        option = ppd.findOption("PageSize")

        assert option.defchoice == "A4"

        os.unlink(path)


