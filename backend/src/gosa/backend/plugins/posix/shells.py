# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.utils import N_
from gosa.common import Environment


class ShellSupport(Plugin):
    """

    Section **posix**

    +------------------+------------+-------------------------------------------------------------+
    + Key              | Format     +  Description                                                |
    +==================+============+=============================================================+
    + shells           | String     + Path to a file containing one shell perl line.              |
    +------------------+------------+-------------------------------------------------------------+

    """
    _target_ = 'misc'

    def __init__(self):
        self.__shells = {}

        # Use a shell source file
        env = Environment.getInstance()
        source = env.config.get('posix.shells', default="/etc/shells")

        with open(source) as f:
            self.__shells =list(filter(lambda y: not y.startswith("#"), [x.strip() for x in f.read().split("\n")]))

    @Command(__help__=N_("Return list of supported shells"))
    def getShellList(self):
        """
        Deliver a list of supported shells.

        ``Return:`` List
        """
        return self.__shells
