# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import TestCase, mock

from gosa.backend.components.jsonrpc_service import JsonRpcHandler
from gosa.backend.plugins.upload.main import *
from tests.RemoteTestCase import RemoteTestCase
from tornado.web import Application, decode_signed_value
import os
from requests_toolbelt.multipart.encoder import MultipartEncoder


class UploadManagerTestCase(TestCase):

    def test_registerUploadPath(self):
        manager = PluginRegistry.getInstance("UploadManager")
        uuid, path = manager.registerUploadPath("admin", "SESSION_ID", "workflow")

        res = manager.get_path_settings(uuid)
        assert res['type'] == "workflow"
        assert res['user'] == "admin"
        assert res['session_id'] == "SESSION_ID"

        manager.unregisterUploadPath(uuid)
        assert manager.get_path_settings(uuid) is None

    def test_garbage_collection(self):
        manager = PluginRegistry.getInstance("UploadManager")
        uuid, path = manager.registerUploadPath("admin", "SESSION_ID", "workflow")

        with mock.patch("gosa.backend.plugins.upload.main.datetime") as m:
            m.datetime.now.return_value = datetime.datetime.now() + datetime.timedelta(minutes=11)
            assert manager.get_path_settings(uuid) is not None
            manager._UploadManager__gc()
            assert manager.get_path_settings(uuid) is None


class UploadHandlerTestCase(RemoteTestCase):

    def get_app(self):
        return Application([('/rpc', JsonRpcHandler), ('/uploads/(?P<uuid>.*)?', UploadHandler)], cookie_secret='TecloigJink4',
                           xsrf_cookies=True)

    def test_upload(self):
        self.login()
        manager = PluginRegistry.getInstance("UploadManager")
        fpath = os.path.join(os.path.dirname(__file__), 'test.jpg')

        with open(fpath, "rb") as f:
            m = MultipartEncoder(
                fields={'field0': ('test.jpg', f, 'text/plain')}
            )
            data = m.to_string()

            # try to use unregistered path
            uuid, path = manager.registerUploadPath("admin", self.session_id, "workflow")
            response = self.fetch("/uploads/unknown_path", method="POST", body=data, headers={
                'Content-Type': m.content_type
            })
            assert response.code == 404
            assert manager.unregisterUploadPath(uuid) is True

            # try to use path from another user
            uuid, path = manager.registerUploadPath("other_user", self.session_id, "workflow")
            response = self.fetch(path, method="POST", body=data, headers={
                'Content-Type': m.content_type
            })
            assert response.code == 403
            assert manager.unregisterUploadPath(uuid) is True

            # try to use path from another session
            uuid, path = manager.registerUploadPath("admin", "other session id", "workflow")
            response = self.fetch(path, method="POST", body=data, headers={
                'Content-Type': m.content_type
            })
            assert response.code == 403
            assert manager.unregisterUploadPath(uuid) is True

            # try to use path for unhandled type
            uuid, path = manager.registerUploadPath("admin", self.session_id, "unknown-type")
            response = self.fetch(path, method="POST", body=data, headers={
                'Content-Type': m.content_type
            })
            assert response.code == 501
            assert manager.unregisterUploadPath(uuid) is True

            # finally a working example
            uuid, path = manager.registerUploadPath("admin", self.session_id, "workflow")
            response = self.fetch(path, method="POST", body=data, headers={
                'Content-Type': m.content_type
            })
            assert response.code == 200
            # path should have been removed by successfully unsigning it
            assert manager.unregisterUploadPath(uuid) is False


