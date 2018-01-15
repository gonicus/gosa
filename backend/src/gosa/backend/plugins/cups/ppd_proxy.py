# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import logging

from zope.interface import implementer

from gosa.common import Environment
from gosa.common.handler import IInterfaceHandler


@implementer(IInterfaceHandler)
class PPDProxy(object):
    """
    PPD backend proxy: this class can be replaced by other implementations e.g. the GOsa proxy
    uses an implementation that caches the PPD files locally
    """
    _priority_ = 10

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    def getPPDURL(self, source_url):
        """ Returns the unmodified source_url """
        return source_url