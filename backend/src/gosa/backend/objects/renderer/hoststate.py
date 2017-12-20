# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import sys

from gosa.backend.objects.renderer import ResultRenderer
from gosa.common.utils import N_


class HostStateRenderer(ResultRenderer):

    @staticmethod
    def getName():
        return "hostStateRenderer"

    @staticmethod
    def render(data):
        overlay = {}
        tooltip = None
        if "status" in data and data["status"] is not None:
            status = data["status"][0]
            if status == "warning":
                overlay["color"] = '#F6BB42'
                overlay["icon"] = "@Ligature/help"
                tooltip = N_("Warning")
            elif status in ["error", "token-expired"]:
                overlay["color"] = '#ED5565'
                overlay["icon"] = "@Ligature/help"
                tooltip = N_("Error") if status == "error" else N_("Token expired")
            elif status == "pending":
                tooltip = N_("Pending installation")
                overlay["color"] = "#AAB2BD"
                overlay["icon"] = "@Ligature/help"
            elif status == "install":
                tooltip = N_("Installing")
                overlay["color"] = "#AAB2BD"
                overlay["icon"] = "@Ligature/sync"
            elif status in ["ready", "discovered"]:
                overlay["color"] = "#8CC152"
                overlay["icon"] = "@Ligature/check"
                tooltip = N_("Ready") if status == "ready" else N_("Discovered")

        res = {"icon": "@Ligature/pc"}
        if "icon" in overlay:
            res["overlay"] = overlay
        if tooltip is not None:
            res["tooltip"] = tooltip

        return res
