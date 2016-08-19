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
from gosa.common import Environment
from gosa.common.event import EventMaker
from gosa.common.components.mqtt_handler import MQTTHandler


class MQTTClientHandler(MQTTHandler):

    def __init__(self):
        super(MQTTClientHandler, self).__init__()
        e = EventMaker()
        goodbye = e.Event(e.ClientLeave(
            e.Id(Environment.getInstance().uuid)
        ))
        self.will_set("%s/client/%s" % (self.domain, self.env.uuid), goodbye)

    def send_message(self, data, topic=None):
        """ Send message to mqtt. """
        if topic is None:
            topic = "%s/client/%s" % (self.domain, self.env.uuid)
        super(MQTTClientHandler, self).send_message(data, topic)

    def send_event(self, data, topic=None):
        """ Send event to mqtt. """
        if topic is None:
            topic = "%s/client/%s" % (self.domain, self.env.uuid)
        super(MQTTClientHandler, self).send_event(data, topic)

    def init_subscriptions(self):
        """ add client subscriptions """
        self.get_client().add_subscription("%s/client/broadcast" % self.domain)
        self.get_client().add_subscription("%s/client/%s" % (self.domain, self.env.uuid))
        # RPC calls from backend
        self.get_client().add_subscription("%s/client/%s/+/to-client" % (self.domain, self.env.uuid))
