# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
The usage of the zope interface is in progress. Currently, it is just used as a
marker.
"""
import zope.interface


class IInterfaceHandler(zope.interface.Interface):
    """ Mark a plugin to be the manager for a special interface """
    pass


class IPluginHandler(zope.interface.Interface):
    """ Mark a plugin to be the manager for a special interface """
    pass
