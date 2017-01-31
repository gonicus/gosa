
# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import logging
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.common.handler import IInterfaceHandler
from zope.interface import implementer


@implementer(IInterfaceHandler)
class Mail(Plugin):
    _priority_ = 0
    _target_ = "core"

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    def send(self, to, subject, message, sender=None):
        msg = {
            'Subject': subject,
            'From': sender if sender is not None else "gosa@localhost",
            'To': to,
            'Message': message
        }

        with open("/tmp/gosa-mail.txt", "a") as f:
            f.write(str(msg)+"\n")