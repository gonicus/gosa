# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.


class Plugin(object):
    """
    The Plugin object is just a marker in the moment: it lacks special
    code. While beeing a marker, it can contain a ``_locale_module_``
    property which indicates the module where the locale is located.

    Example:

        >>> from gosa.common import Environment
        >>> from gosa.common.components import Command, Plugin
        >>> from gosa.common.utils import N_
        >>>
        >>> class SampleModule(Plugin):
        ...
        ...     @Command(__help__=N_("Return a pre-defined message to the caller"))
        ...     def hello(self, name="unknown"):
        ...         return _("Hello %s!") % name

    """
    _locale_module_ = 'gosa.common'

    def get_target(self):
        return self._target_

    def get_locale_module(self):
        return self._locale_module_
