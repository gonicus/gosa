# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import mock

from gosa.backend.objects.index import ObjectInfoIndex
from gosa.common.env import make_session
from tests.GosaTestCase import *
from gosa.backend.objects.backend.back_object import *


class ObjectBackendTestCase(TestCase):

    def setUp(self):
        self.back = ObjectHandler()
        with make_session() as session:
            res = session.query(ObjectInfoIndex.uuid).filter(ObjectInfoIndex.dn == "cn=Frank Reich,ou=people,dc=example,dc=net").one()
            self.user_uuid = res[0]

    def tearDown(self):
        del self.back

    @slow
    def test_load(self):
        res = self.back.load(self.user_uuid,
                             {
                                 'groupMembership': {
                                     'value': ['freich'],
                                     'type': 'String',
                                     'orig': ['freich']
                                 }
                             },
                             {'groupMembership': 'PosixGroup:cn,memberUid=uid'})
        assert 'groupMembership' in res

    def test_extend(self):
        #just a wrapper for the update method
        with mock.patch.object(self.back, 'update') as m:
            self.back.extend('uuid', 'data', 'params', 'foreign_keys')
            m.assert_called_with('uuid', 'data', 'params', dn=None)

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
    @slow
    def test_update(self):

        with pytest.raises(BackendError):
            self.back.update(self.user_uuid,
                                   {'groupMembership': 'String'},
                                   {})
        with pytest.raises(BackendError):
            # wrong uuid
            self.back.update('78475884-c7f2-1035-8262-f535be14d43b',
                                   {
                                       'groupMembership': {
                                           'value': ['freich'],
                                           'type': 'String',
                                           'orig': ['freich']
                                       }
                                   },
                                   {'groupMembership': 'PosixGroup:cn,memberUid=uid'})
        with pytest.raises(EntryNotFound):
            # wrong group
            self.back.update(self.user_uuid,
                             {
                                 'groupMembership': {
                                     'value': ['unknown'],
                                     'type': 'String',
                                     'orig': ['freich']
                                 }
                             },
                             {'groupMembership': 'PosixGroup:cn,memberUid=uid'})

        with mock.patch("gosa.backend.objects.backend.back_object.ObjectProxy") as m:
            self.back.update(self.user_uuid,
                                 {
                                     'groupMembership': {
                                         'value': ['freich'],
                                         'type': 'String',
                                         'orig': ['freich']
                                     }
                                 },
                                 {'groupMembership': 'PosixGroup:cn,memberUid=uid'})
            assert m.return_value.commit.called

            # fake the index search for groups
            mocked_index = mock.MagicMock()
            real_index = PluginRegistry.getInstance('ObjectIndex')

            def search(query, attrs):
                if ('_type' in query or 'or_' in query and '_type' in query['or_']) and 'cn' in query:
                    return [{'dn': 'cn=freich,ou=groups,dc=example,dc=net'}]
                else:
                    return real_index.search(query, attrs)
            mocked_index.search.side_effect = search
            with mock.patch.dict("gosa.backend.objects.proxy.PluginRegistry.modules", {'ObjectIndex': mocked_index}):
                self.back.update(self.user_uuid,
                                 {
                                     'groupMembership': {
                                         'value': ['new', 'add'],
                                         'type': 'String',
                                         'orig': ['freich', 'remove']
                                     }
                                 },
                                 {'groupMembership': 'PosixGroup:cn,memberUid=uid'})
                assert m.return_value.commit.called