# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import mock, TestCase
import pytest
import shutil
import datetime
from gosa.backend.plugins.user.filters import *
from gosa.common.components.jsonrpc_utils import Binary


class UserFiltersTestCase(TestCase):

    def test_ImageProcessor(self):
        # read example image
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "test.jpg"), "r+b") as f:
            byte = f.read()

        user = mock.MagicMock()
        user.uuid = '78475884-c7f2-1035-8262-f535be14d43a'
        user.modifyTimestamp = datetime.datetime.now()
        test_dict = {
            "image": {
                "value": [Binary(byte)]
            }
        }
        image_dir = os.path.join(Environment.getInstance().config.get("user.image-path", "/tmp/images"), user.uuid)

        with mock.patch("gosa.backend.plugins.user.filters.Environment.getInstance") as m_env, \
                mock.patch("gosa.backend.plugins.user.filters.Base.metadata.create_all") as m_create_all, \
                mock.patch("gosa.backend.plugins.user.filters.os.path.exists", return_value=True), \
                mock.patch("gosa.backend.plugins.user.filters.os.path.isdir", return_value=True):
            mocked_db_query = m_env.return_value.getDatabaseSession.return_value.query.return_value.filter.return_value.one_or_none
            mocked_db_query.side_effect = OperationalError(None, None, None)
            filter = ImageProcessor(None)
            filter.process(user, "image", test_dict, "32", "64")
            assert m_create_all.called
            m_create_all.reset_mock()

            mocked_db_query.side_effect = [None, OperationalError(None, None, None)]
            filter.process(user, "image", test_dict, "32")
            assert m_create_all.called

        filter = ImageProcessor(None)

        with pytest.raises(ElementFilterException):
            filter.process(None, None, None)

        with pytest.raises(ElementFilterException), \
                mock.patch("gosa.backend.plugins.user.filters.os.path.exists", return_value=True),\
                mock.patch("gosa.backend.plugins.user.filters.os.path.isdir", return_value=False), \
                mock.patch.object(filter._ImageProcessor__session, "add"), \
                mock.patch.object(filter._ImageProcessor__session, "commit"):
            filter.process(user, "image", test_dict, "32", "64")

        with mock.patch.object(filter._ImageProcessor__session, "add") as ma, \
                mock.patch.object(filter._ImageProcessor__session, "commit") as mc:
            filter.process(user, "image", test_dict, "32", "64")
            assert ma.called
            assert mc.called
            assert os.path.exists(os.path.join(image_dir, "image", "0", "32.jpg"))
            assert os.path.exists(os.path.join(image_dir, "image", "0", "64.jpg"))

        shutil.rmtree(image_dir)

        found = mock.MagicMock()
        found.filter.return_value.one_or_none.return_value.modified = user.modifyTimestamp
        with mock.patch.object(filter._ImageProcessor__session, "query", return_value=found),\
                mock.patch.object(filter._ImageProcessor__session, "add") as ma, \
                mock.patch.object(filter._ImageProcessor__session, "commit") as mc:
            filter.process(user, "image", test_dict, "32", "64")
            assert not ma.called
            assert not mc.called
            assert not os.path.exists(os.path.join(image_dir, "image", "0", "32.jpg"))
            assert not os.path.exists(os.path.join(image_dir, "image", "0", "64.jpg"))

            filter.process(user, "image", {'image': {'value': [Binary(b"wrong binary data")]}}, "32", "64")

        with mock.patch.object(filter._ImageProcessor__session, "add") as ma, \
                mock.patch.object(filter._ImageProcessor__session, "commit") as mc:
            filter.process(user, "image", {'image': {'value': [Binary(b"wrong binary data")]}}, "32", "64")
            assert ma.called
            assert mc.called
            assert not os.path.exists(os.path.join(image_dir, "image", "0", "32.jpg"))
            assert not os.path.exists(os.path.join(image_dir, "image", "0", "64.jpg"))

    def test_LoadDisplayNameState(self):
        filter = LoadDisplayNameState(None)
        testDict = {
            "displayName": {
                "value": []
            },
            "autoDisplayName": {
                "value": [False]
            },
            "sn": {
                "value": ["Surname"]
            },
            "givenName": {
                "value": ["Givenname"]
            }
        }

        (key, valDict) = filter.process(None, "autoDisplayName", testDict.copy())
        assert valDict['autoDisplayName']['value'][0] == True

        testDict["displayName"]["value"] = ["Givenname Surname"]
        (key, valDict) = filter.process(None, "autoDisplayName", testDict.copy())
        assert valDict['autoDisplayName']['value'][0] == True

        testDict["displayName"]["value"] = ["Other name"]
        (key, valDict) = filter.process(None, "autoDisplayName", testDict.copy())
        assert valDict['autoDisplayName']['value'][0] == False

    def test_GenerateDisplayName(self):
        filter = GenerateDisplayName(None)
        testDict = {
            "displayName": {
                "value": []
            },
            "autoDisplayName": {
                "value": [False]
            },
            "sn": {
                "value": ["Surname"]
            },
            "givenName": {
                "value": ["Givenname"]
            }
        }

        (key, valDict) = filter.process(None, None, testDict.copy())
        assert valDict['displayName']['value'] == []

        testDict["autoDisplayName"]["value"] = [True]
        (key, valDict) = filter.process(None, None, testDict.copy())
        assert valDict['displayName']['value'][0] == "Givenname Surname"