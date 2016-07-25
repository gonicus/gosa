# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

from lxml import etree
from gosa.common.components.mqtt_handler import MQTTHandler


class MQTTClientHandler(MQTTHandler):

    def send_message(self, data, topic=None):
        """ Send message via proxy to mqtt. """
        if not isinstance(data, str):
            data = etree.tostring(data)
        if topic is None:
            topic = "%s/client/%s" % (self.domain, self.env.uuid)

        super(MQTTHandler, self).send_message(data, topic)

    def init_subscriptions(self):
        """ add client subscriptions """
        self.get_proxy().add_subscription("%s/client/broadcast" % self.domain)
        self.get_proxy().add_subscription("%s/client/%s" % (self.domain, self.env.uuid))
        self.get_proxy().add_subscription("%s/client/%s/#" % (self.domain, self.env.uuid))