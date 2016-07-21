# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import os.path
from gosa.common import Environment
from gosa.backend.objects.renderer import ResultRenderer


class UserPhotoRenderer(ResultRenderer):

    @staticmethod
    def getName():
        return "userPhotoRenderer"

    @staticmethod
    def render(data):
        env = Environment.getInstance()

        cache_path = env.config.get('user.image-path', default="/var/lib/gosa/images")

        if os.path.exists(os.path.join(cache_path, data['_uuid'], "jpegPhoto", "0", "64.jpg")):
            return "/images/%s/jpegPhoto/0/64.jpg?c=%s" % (data['_uuid'], data["_last_changed"])

        return "/static/default/resources/images/objects/64/user.png"
