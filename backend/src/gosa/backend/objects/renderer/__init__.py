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
from gosa.common.error import ClacksErrorHandler as C


def get_renderers():
    res = {}
    for entry in pkg_resources.iter_entry_points("gosa.object.renderer"):
        module = entry.load()
        res[module.getName()] = module.render

    return res


class ResultRenderer(object):

    @staticmethod
    def getName():
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="getName"))

    @staticmethod
    def render(value):
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="render"))
