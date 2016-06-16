# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import urllib
import hashlib

from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.utils import N_
from gosa.common import Environment


class Gravatar(Plugin):
    """
    Utility class that contains methods needed to retrieve gravatar
    URLs.
    """
    _target_ = 'gravatar'

    def __init__(self):
        env = Environment.getInstance()
        self.env = env

    @Command(__help__=N_("Generate the gravatar URL for the given mail address and size."))
    def getGravatarURL(self, mail, size=40, url="http://www.gonicus.de"):
        """
        Generate the gravatar URL to be used for user pictures on
        demand.

        ========= ======================================
        Parameter Description
        ========= ======================================
        mail      Gravatar's mail address
        size      desired image size
        url       Clickable URL
        ========= ======================================

        ``Return:`` Image URL
        """
        gravatar_url = "http://www.gravatar.com/avatar.php?"
        gravatar_url += urllib.urlencode({
            'gravatar_id': hashlib.md5(mail.lower()).hexdigest(),
            'default': url,
            'size': str(size)})
        return gravatar_url
