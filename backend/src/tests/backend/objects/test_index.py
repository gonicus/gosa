# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from gosa.common.gjson import dumps
from lxml import etree
from unittest import mock, TestCase

from gosa.common.components import ObjectRegistry
from gosa.common.components.mqtt_client import MQTTClient, BaseClient
from gosa.common.components.mqtt_handler import MQTTHandler
from gosa.common.event import EventMaker
from tests.GosaTestCase import *
from gosa.backend.objects.index import *


@slow
class ObjectIndexTestCase(TestCase):

    def setUp(self):
        super(ObjectIndexTestCase, self).setUp()
        self.obj = PluginRegistry.getInstance("ObjectIndex")

    def test_insert(self):
        test = mock.MagicMock()
        test.get_parent_dn.return_value = "dc=example,dc=net"
        test.uuid = '78475884-c7f2-1035-8262-f535be14d43a'
        test.asJSON.return_value = {'uuid': test.uuid}

        with mock.patch.object(self.obj, "_ObjectIndex__save") as m_save,\
                mock.patch.object(self.obj, "_get_object") as m_get_object:
            m_get_object.return_value.can_host.return_value = True
            with pytest.raises(IndexException):
                self.obj.insert(test)
                assert not m_save.called

            test.uuid = 'new-uuid'
            test.asJSON.return_value = {'uuid': test.uuid}
            self.obj.insert(test)
            m_save.assert_called_with({'uuid': 'new-uuid'})

    def test_remove(self):
        test = mock.MagicMock()
        test.uuid = '78475884-c7f2-1035-8262-f535be14d43a'
        with mock.patch.object(self.obj, "remove_by_uuid") as m:
            self.obj.remove(test)
            m.assert_called_with(test.uuid)

    def test_getBaseObjectTypes(self):
        res = self.obj.getBaseObjectTypes()
        assert 'User' in res

    def test_update(self):
        test = mock.MagicMock()
        test.uuid = '78475884-c7f2-1035-8262-f535be14d43b'
        test.asJSON.return_value = {
            'uuid': '78475884-c7f2-1035-8262-f535be14d43a',
            'dn': 'cn=Frank Reich,ou=people,dc=example,dc=de',
            '_adjusted_parent_dn': 'ou=people,dc=example,dc=de'
        }

        with mock.patch.object(self.obj, "_ObjectIndex__save") as ms, \
                mock.patch.object(self.obj._ObjectIndex__session, "commit") as mc,\
                mock.patch.object(self.obj, "remove_by_uuid") as mr:
            with pytest.raises(IndexException):
                self.obj.update(test)
            assert not ms.called
            assert not mc.called
            assert not mr.called

            test.uuid = '7ff15c20-b305-1031-916b-47d262a62cc5'
            test.asJSON.return_value = {
                'uuid': '7ff15c20-b305-1031-916b-47d262a62cc5',
                'dn': 'ou=people,dc=example,dc=de',
                '_adjusted_parent_dn': 'dc=example,dc=de'
            }

            self.obj.update(test)
            assert ms.called
            assert mc.called
            mr.assert_called_with(test.uuid)

        # ObjectIndex needs to be rebuild after this test
        PluginRegistry.getInstance('HTTPService').srv.stop()
        PluginRegistry.shutdown()

        oreg = ObjectRegistry.getInstance()  # @UnusedVariable
        pr = PluginRegistry()  # @UnusedVariable
        cr = PluginRegistry.getInstance("CommandRegistry") # @UnusedVariable

    def test_find(self):

        with pytest.raises(FilterException):
            self.obj.find('admin', 'query')

        res = self.obj.find('admin', {'uuid': '78475884-c7f2-1035-8262-f535be14d43a'}, {'uid': 1})
        assert res[0]['dn'] == "cn=Frank Reich,ou=people,dc=example,dc=net"

    def test_search(self):

        with pytest.raises(Exception):
            self.obj.search({'unsupported_': {'uuid': '7ff15c20-b305-1031-916b-47d262a62cc5',
                                              'dn': 'cn=Frank Reich,ou=people,dc=example,dc=net'}}, {'dn': 1})

        res = self.obj.search({'or_': {'uuid': '7ff15c20-b305-1031-916b-47d262a62cc5',
                                       'dn': 'cn=Frank Reich,ou=people,dc=example,dc=net'}}, {'dn': 1})

        assert len(res) == 2
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in [res[0]['dn'], res[1]['dn']]
        assert 'ou=people,dc=example,dc=net' in [res[0]['dn'], res[1]['dn']]

        res = self.obj.search({'and_': {'uuid': '78475884-c7f2-1035-8262-f535be14d43a',
                                        'dn': 'cn=Frank Reich,ou=people,dc=example,dc=net'}}, {'dn': 1})
        assert len(res) == 1
        assert res[0]['dn'] == 'cn=Frank Reich,ou=people,dc=example,dc=net'

        res = self.obj.search({'_parent_dn': 'ou=people,dc=example,dc=net',
                               'not_': {'dn': 'cn=Frank Reich,ou=people,dc=example,dc=net'}}, {'dn': 1})
        assert len(res) == 1
        assert res[0]['dn'] == 'cn=System Administrator,ou=people,dc=example,dc=net'

        res = self.obj.search({'dn': ['cn=Frank Reich,ou=people,dc=example,dc=net', 'cn=System Administrator%']}, {'dn': 1})
        assert len(res) == 2
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in [res[0]['dn'], res[1]['dn']]
        assert 'cn=System Administrator,ou=people,dc=example,dc=net' in [res[0]['dn'], res[1]['dn']]

        res = self.obj.search({'_parent_dn': ['ou=people,dc=example,dc=net'], 'extension': ['PosixUser']}, {'dn': 1})
        assert len(res) == 1
        assert res[0]['dn'] == 'cn=Frank Reich,ou=people,dc=example,dc=net'

        res = self.obj.search({'uid': ['freich']}, {'dn': 1, 'uid': 1})
        assert len(res) == 1
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']

        res = self.obj.search({'uid': ['freich%']}, {'dn': 1, 'uid': 1})
        assert len(res) == 1
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']

        res = self.obj.search({'uid': 'freich', 'extension': 'PosixUser'}, {'dn': 1})
        assert len(res) == 1
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']

        res = self.obj.search({'uid': 'freich%'}, {'dn': 1})
        assert len(res) == 1
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']

        res = self.obj.search({'dn': 'cn=Frank Reich,ou=people,dc=example,dc=net'}, {'dn': 1})
        assert len(res) == 1
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']

        res = self.obj.search({'dn': 'cn=Frank Reich,ou=people%'}, {'dn': 1})
        assert len(res) == 1
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']

    def test_backend_change_processor(self):
        env = Environment.getInstance()

        e = EventMaker()

        class MessageMock:
            def __init__(self, s_id, topic, message):
                self.sender_id = s_id
                self.topic = topic
                self.payload = dumps({
                    'sender_id': None,
                    'content': message
                })

        def send_change(dn, type, mod_time, new_dn=None):
            if dn is not None:
                if new_dn is not None:
                    event = e.Event(e.BackendChange(
                        e.ModificationTime(mod_time),
                        e.ChangeType(type),
                        e.DN(dn),
                        e.NewDN(new_dn)
                    ))
                else:
                    event = e.Event(e.BackendChange(
                        e.ModificationTime(mod_time),
                        e.ChangeType(type),
                        e.DN(dn)
                    ))

            else:
                event = e.Event(e.BackendChange(
                    e.ModificationTime(mod_time),
                    e.ChangeType(type)
                ))

            m_message = MessageMock(None, '%s/events' % env.domain, etree.tostring(event).decode('utf-8'))
            for client in BaseClient.get_clients():
                client.on_message(None, None, m_message)

        index = PluginRegistry.getInstance("ObjectIndex")
        with mock.patch.object(index, "insert") as m_insert,\
                mock.patch.object(index, "update") as m_update, \
                mock.patch.object(index, "remove_by_uuid") as m_remove_by_uuid:
            send_change(None, "modify", "20150101000000Z")
            assert not m_update.called
            assert not m_insert.called
            assert not m_remove_by_uuid.called

            send_change("cn=Frank Reich,ou=people,dc=example,dc=net", "modify", "20150101000000Z")
            assert m_update.called
            assert not m_insert.called
            assert not m_remove_by_uuid.called
            m_update.reset_mock()

            # unknown user
            send_change("cn=Peter Lustig,ou=people,dc=example,dc=net", "modify", "20150101000000Z")
            assert not m_insert.called
            assert not m_remove_by_uuid.called

            send_change("cn=Peter Lustig,ou=people,dc=example,dc=net", "delete", "20150101000000Z")
            assert m_remove_by_uuid.called
            m_remove_by_uuid.reset_mock()

            send_change("cn=Frank Reich,ou=people,dc=example,dc=net", "add", "20150101000000Z")
            assert m_insert.called
            m_insert.reset_mock()

            with mock.patch.object(index, "_get_object", return_value=mock.MagicMock()):
                send_change("cn=Frank Reich,ou=people,dc=example,dc=net", "moddn", "20150101000000Z", new_dn="cn=Frank Räich,ou=people,"
                                                                                                             "dc=example,dc=net")
                assert m_update.called

    def test_serve(self):
        with mock.patch("gosa.backend.objects.index.ObjectIndex.isSchemaUpdated", return_value=True),\
                mock.patch("gosa.backend.objects.index.Environment.getInstance") as m_env, \
                mock.patch("gosa.backend.objects.index.MqttEventConsumer"):
            m_session = m_env.return_value.getDatabaseSession.return_value
            m_session.query.return_value.one_or_none.return_value = None
            index = ObjectIndex()
            index.serve()

            assert m_session.query.return_value.delete.called
            assert m_session.add.called
            assert m_session.commit.called

            index.stop()
            del index

