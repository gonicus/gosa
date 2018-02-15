# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import logging
from os import path, makedirs

import requests
from urllib3.util import parse_url
from zope.interface import implementer

from gosa.backend.components.httpd import get_server_url
from gosa.backend.objects.index import RegisteredBackend
from gosa.backend.utils import BackendTypes
from gosa.common import Environment
from gosa.common.env import make_session
from gosa.common.handler import IInterfaceHandler
from gosa.common.error import GosaErrorHandler as C


@implementer(IInterfaceHandler)
class PPDProxy(object):
    _priority_ = 10

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.ppd_dir = self.env.config.get("cups.spool", default="/tmp/spool")
        if not path.exists(self.ppd_dir):
            makedirs(self.ppd_dir)
        self.base_url = "%s/ppd-proxy/" % get_server_url()

    def getPPDURL(self, source_url):
        """
        Downloads the source_url, stores it locally and returns the local URL

        :param source_url: remote PPD URL
        :return: local URL to the cached PPD
        """
        source = parse_url(source_url)
        host = source.host
        if host is None or host == "localhost":
            # no host: we assume that the PPD can be found on the current active master backend
            with make_session() as session:
                # get any other registered backend
                master_backend = session.query(RegisteredBackend) \
                    .filter(RegisteredBackend.uuid != self.env.core_uuid,
                            RegisteredBackend.type == BackendTypes.active_master).first()
                if master_backend is None:
                    self.log.error(C.make_error("NO_MASTER_BACKEND_FOUND"))
                    return source_url

                # Try to log in with provided credentials
                url = parse_url(master_backend.url)
                host = url.host

        # check if file exists locally
        rel_path = source.path[1:] if source.path.startswith("/") else source.path
        local_path = path.join(self.ppd_dir, host, rel_path)
        if not path.exists(local_path):
            # cache locally
            try:
                r = requests.get(source_url)
                if r.ok:
                    local_dir = path.dirname(local_path)
                    if not path.exists(local_dir):
                        makedirs(local_dir)
                    with open(local_path, "w") as f:
                        f.write(r.text)
                else:
                    self.log.error("requesting PPD from %s failed with status code: %s" % (source_url, r.status_code))
                    return source_url
            except requests.exceptions.ConnectionError as e:
                self.log.error("requesting PPD from %s failed with error: %s" % (source_url, str(e)))
                return source_url

        return "%s%s/%s" % (self.base_url, host, rel_path)
