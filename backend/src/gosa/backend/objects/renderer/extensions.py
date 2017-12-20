# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from gosa.backend.objects.renderer import ResultRenderer


class ExtensionRenderer(ResultRenderer):

    @staticmethod
    def getName():
        return "extensions"

    @staticmethod
    def render(data):
        if "_extensions" in data:
            return (", ".join(["<a href='gosa://%s/%s?edit'>%s</a>" % (data['dn'][0], i, i) for i in data['_extensions']]))

        return ""
