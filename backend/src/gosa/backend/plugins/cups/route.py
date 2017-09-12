# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from gosa.common import Environment
from gosa.common.hsts_request_handler import HSTSStaticFileHandler


class PPDHandler(HSTSStaticFileHandler):
    dir = None

    def initialize(self):
        env = Environment.getInstance()
        self.dir = env.config.get("cups.spool", default="/tmp/spool")
        super(PPDHandler, self).initialize(self.dir)

    def get(self, path, include_body=True):
        self.set_header("Content-Type", "application/vnd.cups-ppd")
        super(PPDHandler, self).get(path, include_body)
