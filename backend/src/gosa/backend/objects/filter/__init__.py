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
    FILTER_NO_INSTANCE=N_("No filter instance for '%(filter)s' found")
    ))


def get_filter(name):
    for entry in pkg_resources.iter_entry_points("gosa.object.filter"):
        module = entry.load()
        if module.__name__ == name:
            return module

    raise KeyError(C.make_error("FILTER_NO_INSTANCE", filter=name))


class ElementFilter(object):

    def __init__(self, obj):  # pragma: nocover
        pass

    def process(self, obj, key, value, *args):  # pragma: nocover
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", method="process"))

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
