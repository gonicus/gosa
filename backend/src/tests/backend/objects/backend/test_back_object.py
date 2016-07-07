# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import mock
import pytest
from tests.GosaTestCase import GosaTestCase
from gosa.backend.objects.backend.back_object import *


class ObjectBackendTestCase(GosaTestCase):

    def setUp(self):
        self.back = ObjectHandler()

    def tearDown(self):
        del self.back

    def test_load(self):
        super(ObjectBackendTestCase, self).setUp()
        res = self.back.load('78475884-c7f2-1035-8262-f535be14d43a',
                             {'groupMembership': 'String'},
                             {'groupMembership': 'PosixGroup:cn,memberUid=uid'})

        assert 'groupMembership' in res
        super(ObjectBackendTestCase, self).tearDown()

    def test_extend(self):
        #just a wrapper for the update method
        with mock.patch.object(self.back, 'update') as m:
            self.back.extend('uuid', 'data', 'params', 'foreign_keys')
            m.assert_called_with('uuid', 'data', 'params')

    def test_retract(self):
        #just a wrapper for the update method
        with mock.patch.object(self.back, 'update') as m:
            self.back.retract('uuid', {
                'attr1': {
                    'value': ['test']
                }
            }, 'params')
            m.assert_called_with('uuid', {
                'attr1': {
                    'value': []
                }
            }, 'params')

    def test_remove(self):
        #just a wrapper for the retract method
        with mock.patch.object(self.back, 'retract') as m:
            self.back.remove('uuid', 'data', 'params')
            m.assert_called_with('uuid', 'data', 'params')

    # TODO: must be completed
    # def test_update(self):
    #     super(ObjectBackendTestCase, self).setUp()
    #
    #     with pytest.raises(BackendError):
    #         self.back.update('78475884-c7f2-1035-8262-f535be14d43a',
    #                                {'groupMembership': 'String'},
    #                                {})
    #
    #     res = self.back.update('78475884-c7f2-1035-8262-f535be14d43a',
    #                          {'groupMembership': 'String'},
    #                          {'groupMembership': 'PosixGroup:cn,memberUid=uid'})
    #     print(res)
    #     assert False
    #     super(ObjectBackendTestCase, self).tearDown()

    def test_rest(self):
        assert self.back.identify_by_uuid('uuid', {}) is False
        assert self.back.identify('dn', {}) is False
        assert self.back.query('base', 'scope', {}) == []
        assert self.back.exists('misc') is False
        assert self.back.move('uuid', 'new_base') is False
        assert self.back.create('base', [], []) is None
        assert self.back.uuid2dn('uuid') is None
        assert self.back.dn2uuid('dn') is None
        assert self.back.get_timestamps('dn') == (None, None)
        assert self.back.is_uniq(None, None, None) is False
        assert self.back.get_uniq_dn(None, None, None, None) is None
        with pytest.raises(BackendError):
            self.back.get_next_id(None)