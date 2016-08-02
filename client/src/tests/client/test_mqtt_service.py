# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import pytest
from unittest import TestCase, mock
from gosa.client.mqtt_service import *
from gosa.common import Environment


class ClientMqttServiceTestCase(TestCase):

    def setUp(self):
        self.mqtt = MQTTClientService()
        self.mqtt.serve()

    def test_handle_message(self):
        pass