# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import pytest
from unittest import mock
from tests.GosaTestCase import GosaTestCase
from gosa.backend.objects.index import *


class ObjectBackendTestCase(GosaTestCase):

    def setUp(self):
        self.obj = ObjectIndex()

    def tearDown(self):
        del self.obj

    def test_insert(self):
        test = mock.MagicMock()
        test.uuid = '78475884-c7f2-1035-8262-f535be14d43a'
        test.toJSON.return_value = {'uuid': '78475884-c7f2-1035-8262-f535be14d43b'}
        with pytest.raises(IndexException),\
                mock.patch.object(self.obj, "_ObjectIndex__save") as m:
            self.obj.insert(test)
            assert not m.called

        test.uuid = '78475884-c7f2-1035-8262-f535be14d43b'
        self.obj.insert(test)
        m.assert_called_with({'uuid': '78475884-c7f2-1035-8262-f535be14d43b'})