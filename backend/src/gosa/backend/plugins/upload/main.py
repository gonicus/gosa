
# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from uuid import uuid4
import logging
import datetime

import pkg_resources
from gosa.common import Environment
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.components import PluginRegistry
from gosa.common.handler import IInterfaceHandler
from gosa.common.hsts_request_handler import HSTSRequestHandler
from gosa.common.utils import N_
from tornado import web
from tornadostreamform.multipart_streamer import MultiPartStreamer
from zope.interface import implementer


@implementer(IInterfaceHandler)
class UploadManager(Plugin):
    _priority_ = 0
    _target_ = "core"
    __tmp_paths = {}
    __upload_handlers = {}

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing upload manager")

    def serve(self):
        sched = PluginRegistry.getInstance("SchedulerService").getScheduler()
        sched.add_interval_job(self.__gc, minutes=10, tag='_internal', jobstore="ram")

        # register upload handlers
        for entry in pkg_resources.iter_entry_points("gosa.upload_handler"):
            module = entry.load()
            self.__upload_handlers[entry.name] = module()

    @Command(needsUser=True, needsSession=True, __help__=N_("Registers a temporary upload path"))
    def registerUploadPath(self, user, session_id, type):
        uuid = str(uuid4())
        self.__tmp_paths[uuid] = {
            'user': user,
            'session_id': session_id,
            'type': type,
            'valid_until': datetime.datetime.now() + datetime.timedelta(minutes=10)
        }
        return uuid, "/uploads/%s" % uuid

    def get_path_settings(self, uuid):
        return self.__tmp_paths[uuid] if uuid in self.__tmp_paths else None

    def unregisterUploadPath(self, uuid):
        if uuid in self.__tmp_paths:
            del self.__tmp_paths[uuid]
            return True
        else:
            return False

    def get_upload_handler(self, type):
        return self.__upload_handlers[type] if type in self.__upload_handlers else None

    def __gc(self):
        for uuid in list(self.__tmp_paths):
            if self.__tmp_paths[uuid]['valid_until'] < datetime.datetime.now():
                # outdated
                del self.__tmp_paths[uuid]


@web.stream_request_body
class UploadHandler(HSTSRequestHandler):
    """
    Handle uploads to the backend like workflows
    """
    current_uuid = None
    path = None
    temp_file = None
    upload_handler = None
    ps = None

    def prepare(self):
        uuid = self.request.uri[len('/uploads/'):]
        manager = PluginRegistry.getInstance("UploadManager")
        path_settings = manager.get_path_settings(uuid)
        if path_settings is None:
            # invalid temporary path used
            raise web.HTTPError(status_code=404, reason="Temporary upload path does not exist")

        # check user and session
        if path_settings['user'] != self.get_secure_cookie('REMOTE_USER').decode('ascii'):
            raise web.HTTPError(status_code=403, reason="Temporary upload path was created for another user")
        if path_settings['session_id'] != self.get_secure_cookie('REMOTE_SESSION').decode('ascii'):
            raise web.HTTPError(status_code=403, reason="Temporary upload path was created for another session")

        # check if we can handle the upload type
        self.upload_handler = manager.get_upload_handler(path_settings['type'])
        if self.upload_handler is None:
            raise web.HTTPError(status_code=501, reason="No upload handler registered for type '%s'" % path_settings['type'])
        else:
            try:
                total = int(self.request.headers.get("Content-Length", "0"))
            except KeyError:
                total = 0
            self.ps = MultiPartStreamer(total)

    def data_received(self, chunk):
        self.ps.data_received(chunk)

    def post(self, uuid):
        try:
            self.ps.data_complete() # You MUST call this to close the incoming stream.
            # Here can use self.ps to access the fields and the corresponding ``StreamedPart`` objects.
            self.upload_handler.handle_upload(self.ps.get_parts_by_name('file')[0], self.request)

            # cleanup
            PluginRegistry.getInstance("UploadManager").unregisterUploadPath(uuid)
            self.upload_handler = None

        finally:
            # When ready, don't forget to release resources.
            self.ps.release_parts()
            self.finish() # And of course, you MUST call finish()


class IUploadFileHandler(object):
    def handle_upload(self, file, request):  # pragma: nocover
        raise NotImplementedError()
