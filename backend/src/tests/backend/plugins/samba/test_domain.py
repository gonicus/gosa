# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
import pytest
from types import SimpleNamespace
from gosa.backend.plugins.samba.domain import *

# TODO: write other tests when ACLs are ready

@unittest.mock.patch.object(PluginRegistry, 'getInstance')
def test_IsValidSambaDomainName(mockedInstance):
    # mock the whole lookup in the ObjectIndex to return True
    MyObject = type('MyObject', (object,), {})
    index = MyObject()
    def search(param1, param2):
        res = MyObject()
        res.count = lambda: True
        return res
    index.search = search

    mockedInstance.return_value = index

    check = IsValidSambaDomainName(None)

    (res, errors) = check.process(None, None, ["test"])
    assert res == True
    assert len(errors) == 0

    # mockup everything to return False
    index = MyObject()

    def search(param1, param2):
        res = MyObject()
        res.count = lambda: False
        return res

    index.search = search
    mockedInstance.return_value = index

    (res, errors) = check.process(None, None, ["test"])
    assert res == False
    assert len(errors) == 1