# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from zope.interface import Interface, implements


class IResume(Interface):

    def __init__(self):
        pass


class Resume(object):
    implements(IResume)

    def __init__(self):
        pass
