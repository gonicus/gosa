# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from lxml.builder import ElementMaker


def EventMaker():
    """
    Returns the event skeleton object which can be directly used for
    extending with event data.
    """
    return ElementMaker(namespace="http://www.gonicus.de/Events", nsmap={None: "http://www.gonicus.de/Events"})
