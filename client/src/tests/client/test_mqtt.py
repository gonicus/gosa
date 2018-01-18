# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import TestCase, mock
from gosa.common.mqtt import *
from gosa.common import Environment


class ClientMqttTestCase(TestCase):

    def test_send_message(self):
        mqtt = MQTTClientHandler()
        env = Environment.getInstance()

        with mock.patch("gosa.client.mqtt.MQTTHandler.send_message") as m:
            mqtt.send_message("test-data")
            m.assert_called_with("test-data", "%s/client/%s" % (env.domain, env.uuid), qos=0)

            m.reset_mock()
            mqtt.send_message("test-data", topic="test/topic")
            m.assert_called_with("test-data", "test/topic", qos=0)

    def test_send_event(self):
        mqtt = MQTTClientHandler()
        env = Environment.getInstance()

        with mock.patch("gosa.client.mqtt.MQTTHandler.send_event") as m:
            mqtt.send_event("test-data")
            m.assert_called_with("test-data", "%s/client/%s" % (env.domain, env.uuid), qos=0)

            m.reset_mock()
            mqtt.send_event("test-data", topic="test/topic")
            m.assert_called_with("test-data", "test/topic", qos=0)
