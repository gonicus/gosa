# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.backend.plugins.misc.filter_validators import *

class FilterValidatorTests(unittest.TestCase):

    def test_IsValidHostName(self):
        filter = IsValidHostName(None)
        (res, errors) = filter.process(None, None, ["www.gonicus.de"])
        assert res == True
        assert len(errors) == 0

        (res, errors) = filter.process(None, None, ["1www.gonicus.de"])
        assert res == False
        assert len(errors) == 1

    @unittest.mock.patch.object(PluginRegistry, 'getInstance')
    def test_IsExistingDN(self, mockedRegistry):
        # mockup ObjectIndex.search
        MyIndex = type('MyIndex', (object,), {})
        index = MyIndex()
        found = unittest.mock.MagicMock(autoSpec=True, create=True)
        found.count.return_value = 0
        def search(param1, param2):
            return found
        index.search = search
        mockedRegistry.return_value = index

        # start the tests
        filter = IsExistingDN(None)
        (res, errors) = filter.process(None, None, ["test"])
        assert res == False
        assert len(errors) == 1

        found.count.return_value = 1
        (res, errors) = filter.process(None, None, ["test"])
        assert res == True
        assert len(errors) == 0

    @unittest.mock.patch.object(PluginRegistry, 'getInstance')
    def test_IsExistingDnOfType(self, mockedRegistry):
        # mockup ObjectIndex.search
        MyIndex = type('MyIndex', (object,), {})
        index = MyIndex()
        found = unittest.mock.MagicMock(autoSpec=True, create=True)
        found.count.return_value = 0

        def search(param1, param2):
            return found

        index.search = search
        mockedRegistry.return_value = index

        # start the tests
        filter = IsExistingDnOfType(None)
        (res, errors) = filter.process(None, None, ["test"], "type")
        assert res == False
        assert len(errors) == 1

        found.count.return_value = 1
        (res, errors) = filter.process(None, None, ["test"], "type")
        assert res == True
        assert len(errors) == 0

    @unittest.mock.patch.object(PluginRegistry, 'getInstance')
    def test_ObjectWithPropertyExists(self, mockedRegistry):
        # mockup ObjectIndex.search
        MyIndex = type('MyIndex', (object,), {})
        index = MyIndex()
        found = unittest.mock.MagicMock(autoSpec=True, create=True)
        found.count.return_value = 0

        def search(param1, param2):
            return found

        index.search = search
        mockedRegistry.return_value = index

        # start the tests
        filter = ObjectWithPropertyExists(None)
        (res, errors) = filter.process(None, None, ["test"], "type", "attr")
        assert res == False
        assert len(errors) == 1

        found.count.return_value = 1
        (res, errors) = filter.process(None, None, ["test"], "type", "attr")
        assert res == True
        assert len(errors) == 0
