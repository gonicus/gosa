# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

__import__('pkg_resources').declare_namespace(__name__)
import pkg_resources
from gosa.common.utils import N_
from gosa.common.error import GosaErrorHandler as C


C.register_codes(dict(
    COMPARATOR_NO_INSTANCE=N_("No comparator instance for '%(comparator)s' found")
    ))


def get_comparator(name):
    for entry in pkg_resources.iter_entry_points("gosa.object.comparator"):

        module = entry.load()
        if module.__name__ == name:
            return module

    raise KeyError(C.make_error("COMPARATOR_NO_INSTANCE", comparator=name))


class ElementComparator(object):

    def __init(self, obj):  # pragma: nocover
        pass

    def process(self, *args, **kwargs):  # pragma: nocover
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="process"))

    def __copy__(self):  # pragma: nocover
        """
        Do not make copies of ourselves.
        """
        return self

    def __deepcopy__(self, memo):  # pragma: nocover
        """
        Do not make copies of ourselves.
        """
        return self
