# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import os
from unittest import TestCase, mock

import pytest

from gosa.plugins.goto.network import *

@pytest.mark.skipif('TRAVIS' in os.environ and os.environ['TRAVIS'] == "true", reason="Gives strange results inside the docker container")
class GotoNetworkUtilsTestCase(TestCase):

    def setUp(self):
        self.network = NetworkUtils()

    def test_networkCompletion(self):
        with mock.patch("gosa.plugins.goto.network.socket.gethostbyname", return_value="127.0.0.1"):
            res = self.network.networkCompletion("localhost")
            assert res['ip'] == "127.0.0.1"
            assert res['mac'] == "None"

            with mock.patch("gosa.plugins.goto.network.subprocess.Popen") as m_sub:

                # simulate by arp
                arp_res = (b"10.3.64.1                ether   ee:b4:ce:64:81:c3   C                     enp0s25\n"+
                           b"10.3.64.8                ether   52:45:89:a6:9e:fa   C                     enp0s25\n"+
                           b"10.3.64.92               ether   f6:ae:1b:f1:35:1e   C                     enp0s25\n"+
                           b"10.3.64.34               ether   00:18:51:ea:2a:6e   C                     enp0s25\n"+
                           b"127.0.0.1                ether   01:02:03:04:05:0a   C                     enp0s25\n", "err")

                m_sub.return_value.communicate.return_value = arp_res
                res = self.network.networkCompletion("localhost")
                assert res['ip'] == "127.0.0.1"
                assert res['mac'] == "01:02:03:04:05:0a"

                counter = 0

                def popen(params, stdout=None, stderr=None):
                    nonlocal counter
                    result = mock.MagicMock()
                    if params[0] == "arp":
                        result.communicate.return_value = (b"", "") if counter == 0 else arp_res
                        counter += 1
                    elif params[0] == "ping":
                        result.communicate.return_value = (b"", "")
                    return result

                m_sub.side_effect = popen

                # simulate that a ping is needed for the arp command to work
                res = self.network.networkCompletion("localhost")
                assert res['ip'] == "127.0.0.1"
                assert res['mac'] == "01:02:03:04:05:0a"

    def test_getMacManufacturer(self):
        assert self.network.getMacManufacturer('3c:97:0e:ea:16:70') == "Wistron InfoComm(Kunshan)Co.,Ltd."
        assert self.network.getMacManufacturer('ee:b4:ce:64:81:c3') is None
