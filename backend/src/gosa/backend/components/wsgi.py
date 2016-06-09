#!/usr/bin/env python
# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
The WsgiApplication starts and serves the Flask application
through a gunicorn server.
"""
from __future__ import unicode_literals

import gunicorn.app.base
from gunicorn import util

from gunicorn.six import iteritems

class WsgiApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app_uri, options=None):
        self.options = options or {}
        self.app_uri = app_uri
        super(WsgiApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        # load the app
        return util.import_app(self.app_uri)
