# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import base64
from unittest import mock, TestCase
import pytest
import shutil
import datetime
import os
from gosa.backend.plugins.user.filters import GenerateDisplayName, ImageProcessor, LoadDisplayNameState, OperationalError, Environment, \
    ElementFilterException, MarshalLogonScript, UnmarshalLogonScript
from gosa.common.components.jsonrpc_utils import Binary


class UserFiltersTestCase(TestCase):

    def test_ImageProcessor(self):
        # read example image
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "test.jpg"), "r+b") as f:
            byte = f.read()

        user = mock.MagicMock()
        user.uuid = 'fae09b6a-914b-1037-8941-b59a822cf04a'
        user.modifyTimestamp = datetime.datetime.now()
        test_dict = {
            "image": {
                "value": [Binary(byte)]
            }
        }
        image_dir = os.path.join(Environment.getInstance().config.get("user.image-path", "/tmp/images"), user.uuid)
        tmp_image = mock.MagicMock()

        with mock.patch("gosa.backend.plugins.user.filters.Base.metadata.create_all") as m_create_all, \
                mock.patch("gosa.backend.plugins.user.filters.os.path.exists", return_value=True), \
                mock.patch("gosa.backend.plugins.user.filters.os.path.isdir", return_value=True), \
                mock.patch("gosa.backend.plugins.user.filters.ImageOps.fit", return_value=tmp_image):
            filter = ImageProcessor(None)
            with mock.patch("gosa.backend.plugins.user.filters.make_session") as m:
                mocked_db_query = m.return_value.__enter__.return_value.query.return_value.filter.return_value.one_or_none
                mocked_db_query.side_effect = OperationalError(None, None, None)

                filter.process(user, "image", test_dict, "32", "64")
                assert m_create_all.called
                m_create_all.reset_mock()

                mocked_db_query.side_effect = [None, OperationalError(None, None, None)]
                filter.process(user, "image", test_dict, "32")
                assert m_create_all.called
                assert tmp_image.save.called

        filter = ImageProcessor(None)

        with pytest.raises(ElementFilterException):
            filter.process(None, None, None)

        with pytest.raises(ElementFilterException), \
                mock.patch("gosa.backend.plugins.user.filters.os.path.exists", return_value=True),\
                mock.patch("gosa.backend.plugins.user.filters.os.path.isdir", return_value=False), \
                mock.patch("gosa.backend.plugins.user.filters.make_session"):
            filter.process(user, "image", test_dict, "32", "64")

        with mock.patch("gosa.backend.plugins.user.filters.make_session") as m:
            m_session = m.return_value.__enter__.return_value
            m_session.query.return_value.filter.return_value.one_or_none.return_value = None
            filter.process(user, "image", test_dict, "32", "64")
            assert m_session.add.called
            assert m_session.commit.called
            assert os.path.exists(os.path.join(image_dir, "image", "0", "32.jpg"))
            assert os.path.exists(os.path.join(image_dir, "image", "0", "64.jpg"))

        shutil.rmtree(image_dir)

        found = mock.MagicMock()
        found.filter.return_value.one_or_none.return_value.modified = user.modifyTimestamp
        with mock.patch("gosa.backend.plugins.user.filters.make_session") as m:
            m_session = m.return_value.__enter__.return_value
            m_session.query.return_value = found
            filter.process(user, "image", test_dict, "32", "64")
            assert not m_session.add.called
            assert not m_session.commit.called
            assert not os.path.exists(os.path.join(image_dir, "image", "0", "32.jpg"))
            assert not os.path.exists(os.path.join(image_dir, "image", "0", "64.jpg"))

            filter.process(user, "image", {'image': {'value': [Binary(b"wrong binary data")]}}, "32", "64")

        with mock.patch("gosa.backend.plugins.user.filters.make_session") as m:
            m_session = m.return_value.__enter__.return_value
            m_session.query.return_value.filter.return_value.one_or_none.return_value = None
            filter.process(user, "image", {'image': {'value': [Binary(b"wrong binary data")]}}, "32", "64")
            assert m_session.add.called
            assert m_session.commit.called
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

    def test_MarshalLogonScript(self):
        filter = MarshalLogonScript(None)

        testDict = {
            "logonScript": {
                "value": []
            },
            "script": {
                "value": ["some script"]
            },
            "scriptName": {
                "value": ["test"]
            },
            "scriptUserEditable": {
                "value": [True]
            },
            "scriptLast": {
                "value": [True]
            },
            "scriptPriority": {
                "value": [1]
            }
        }

        (key, valDict) = filter.process(None, "logonScript", testDict.copy())
        assert valDict['logonScript']['value'][0] == "test|OL|1|%s" % base64.b64encode("some script".encode("utf-8")).decode()

    def test_UnmarshalLogonScript(self):
        filter = UnmarshalLogonScript(None)

        testDict = {
            "logonScript": {
                "value": ["test|OL|1|%s" % base64.b64encode("some script".encode("utf-8")).decode() ]
            },
            "script": {
                "value": []
            },
            "scriptName": {
                "value": []
            },
            "scriptUserEditable": {
                "value": []
            },
            "scriptLast": {
                "value": []
            },
            "scriptPriority": {
                "value": []
            }
        }

        (key, valDict) = filter.process(None, "logonScript", testDict.copy())
        assert valDict['script']['value'][0] == "some script"
        assert valDict['scriptName']['value'][0] == "test"
        assert valDict['scriptUserEditable']['value'][0] is True
        assert valDict['scriptLast']['value'][0] is True
        assert valDict['scriptPriority']['value'][0] == 1
