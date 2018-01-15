# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import mock, TestCase

import datetime
from gosa.backend.components.jsonrpc_objects import JSONRPCObjectMapper, ObjectRegistry
from gosa.common.components import PluginRegistry
from tests.GosaTestCase import *


@slow
class JSONRPCObjectMapperTestCase(TestCase):
    refs = []

    def setUp(self):
        super(JSONRPCObjectMapperTestCase, self).setUp()
        self.mapper = JSONRPCObjectMapper()
        self.mocked_resolver = mock.MagicMock()
        self.mocked_resolver.return_value.check.return_value = True
        self.mocked_resolver.return_value.isAdmin.return_value = False
        self.patcher = mock.patch.dict(PluginRegistry.modules, {'ACLResolver': self.mocked_resolver})
        self.patcher.start()
        self.refs = []

    def tearDown(self):
        for ref in self.refs:
            try:
                self.mapper.closeObject('admin', ref)
            except ValueError:
                pass
        self.patcher.stop()
        super(JSONRPCObjectMapperTestCase, self).tearDown()

    def test_listObjectOIDs(self):
        res = self.mapper.listObjectOIDs()
        assert 'object' in res
        assert 'workflow' in res
        assert len(res) == 2

    def openObject(self, *args, **kwargs):
        res = self.mapper.openObject(*args, **kwargs)
        self.refs.append(res['__jsonclass__'][1][1])
        return res

    def reloadObject(self, *args, **kwargs):
        res = self.mapper.reloadObject(*args, **kwargs)
        self.refs.remove(args[1])
        self.refs.append(res['__jsonclass__'][1][1])
        return res

    def closeObject(self, user, ref):
        res = self.mapper.closeObject(user, ref)
        self.refs.remove(ref)
        return res

    def test_openObject(self):
        res = self.openObject('admin', None, 'object', 'dc=example,dc=net')
        assert res['dc'] == "example"

        with pytest.raises(Exception):
            self.openObject('admin', None, 'object', 'dc=example,dc=net')

    def test_closeObject(self):
        res = self.openObject('admin', None, 'object', 'dc=example,dc=net')

        with pytest.raises(ValueError):
            self.closeObject('admin', 'unknown')

        with pytest.raises(ValueError):
            self.closeObject('someone else', res["__jsonclass__"][1][1])

        self.closeObject('admin', res["__jsonclass__"][1][1])

        # as a workaround for checking if its not loaded anymore we try to reload it
        with pytest.raises(ValueError):
            self.reloadObject('admin', res["__jsonclass__"][1][1])

    def test_continueObjectEditing(self):
        res = self.openObject('admin', 'session-uuid', 'object', 'dc=example,dc=net')

        with pytest.raises(ValueError):
            self.mapper.continueObjectEditing('admin', 'unknown_ref')

        with pytest.raises(ValueError):
            self.mapper.continueObjectEditing('other_user', res["__jsonclass__"][1][1])

        ref = self.mapper._JSONRPCObjectMapper__get_ref(res["__jsonclass__"][1][1])
        before = ref['last_interaction'] if 'last_interaction' in ref else ref['created']
        self.mapper.continueObjectEditing('admin', res["__jsonclass__"][1][1])
        assert before != ref['last_interaction']

        ref['mark_for_deletion'] = datetime.datetime.now() + datetime.timedelta(seconds=29)
        self.mapper.continueObjectEditing('admin', res["__jsonclass__"][1][1])
        assert 'mark_for_deletion' not in ref

    def test_checkObjectRef(self):
        res = self.openObject('admin', 'session-uuid', 'object', 'dc=example,dc=net')
        ref = self.mapper._JSONRPCObjectMapper__get_ref(res["__jsonclass__"][1][1])
        assert self.mapper.checkObjectRef('admin', 'new-session-uuid', res["__jsonclass__"][1][1]) is True
        assert ref['session_id'] == "new-session-uuid"

        self.closeObject('admin', res["__jsonclass__"][1][1])
        assert self.mapper.checkObjectRef('admin', 'new-session-uuid', res["__jsonclass__"][1][1]) is False

    def test_getObjectProperty(self):
        res = self.openObject('admin', None, 'object', 'dc=example,dc=net')
        ref = res["__jsonclass__"][1][1]

        with pytest.raises(ValueError):
            self.mapper.getObjectProperty('admin', 'unknown', 'prop')

        with pytest.raises(ValueError):
            self.mapper.getObjectProperty('admin', ref, 'prop')

        with pytest.raises(ValueError):
            self.mapper.getObjectProperty('someone else', ref, 'description')

        assert self.mapper.getObjectProperty('admin', ref, 'description') == "Example"

    def test_setObjectProperty(self):
        res = self.openObject('admin', "session-uuid", 'object', 'cn=Frank Reich,ou=people,dc=example,dc=net')
        ref = res["__jsonclass__"][1][1]

        with pytest.raises(ValueError):
            self.mapper.setObjectProperty('admin', 'unknown', 'prop', 'val')

        with pytest.raises(ValueError):
            self.mapper.setObjectProperty('admin', ref, 'prop', 'val')

        with pytest.raises(ValueError):
            self.mapper.setObjectProperty('someone else', ref, 'description', 'val')

        objdesc = self.mapper._JSONRPCObjectMapper__get_ref(res["__jsonclass__"][1][1])
        objdesc['mark_for_deletion'] = datetime.datetime.now() + datetime.timedelta(seconds=29)

        self.mapper.setObjectProperty('admin', ref, 'uid', 'val')
        assert self.mapper.getObjectProperty('admin', ref, 'uid') == "val"
        assert 'mark_for_deletion' not in objdesc

        # undo
        self.mapper.setObjectProperty('admin', ref, 'uid', 'admin')
        assert self.mapper.getObjectProperty('admin', ref, 'uid') == "admin"

    def test_reloadObjectProperty(self):
        res = self.openObject('admin', None, 'object', 'dc=example,dc=net')
        uuid = res['uuid']
        ref = res["__jsonclass__"][1][1]

        with pytest.raises(ValueError):
            self.reloadObject('someone else', ref)

        res = self.reloadObject('admin', ref)
        assert uuid == res['uuid']
        assert ref != res["__jsonclass__"][1][1]

    def test_dispatchObjectMethod(self):
        res = self.openObject('admin', None, 'object', 'cn=Frank Reich,ou=people,dc=example,dc=net')
        ref = res["__jsonclass__"][1][1]

        with pytest.raises(ValueError):
            self.mapper.dispatchObjectMethod('admin', None, 'wrong_ref', 'lock')

        with pytest.raises(ValueError):
            self.mapper.dispatchObjectMethod('admin', None, ref, 'wrong_method')

        with pytest.raises(ValueError):
            self.mapper.dispatchObjectMethod('someone_else', None, ref, 'lock')

        # mock a method in the object

        with mock.patch('gosa.backend.plugins.password.manager.ObjectProxy') as m:
            user = m.return_value
            user.passwordMethod = "MD5"
            self.mapper.dispatchObjectMethod('admin', None, ref, 'changePassword', 'Test')
            assert user.userPassword
            assert user.commit.called

    def test_diffObject(self):
        assert self.mapper.diffObject('admin', 'unkown_ref') is None

        res = self.openObject('admin', None, 'object', 'cn=Frank Reich,ou=people,dc=example,dc=net')
        ref = res["__jsonclass__"][1][1]

        with pytest.raises(ValueError):
            self.mapper.diffObject('someone_else', ref)

        self.mapper.setObjectProperty('admin', ref, 'uid', 'val')
        delta = self.mapper.diffObject('admin', ref)
        assert 'uid' in delta['attributes']['changed']

    def test_removeObject(self):
        res = self.openObject('admin', None, 'object', 'cn=Frank Reich,ou=people,dc=example,dc=net')
        ref = res["__jsonclass__"][1][1]

        with pytest.raises(Exception):
            self.mapper.removeObject('admin','object', 'cn=Frank Reich,ou=people,dc=example,dc=net')

        self.closeObject('admin', ref)

        with mock.patch.dict(ObjectRegistry.objects['object'], {'object': mock.MagicMock()}):
            mockedObject = ObjectRegistry.objects['object']['object'].return_value
            self.mapper.removeObject('admin', 'object', 'cn=Frank Reich,ou=people,dc=example,dc=net')
            assert mockedObject.remove.called

    def test_garbage_collection(self):
        res = self.openObject('admin', 'session-uuid', 'object', 'cn=Frank Reich,ou=people,dc=example,dc=net')
        ref = res["__jsonclass__"][1][1]
        obj_desc = self.mapper._JSONRPCObjectMapper__get_ref(res["__jsonclass__"][1][1])

        obj_desc['last_interaction'] = datetime.datetime.now() - datetime.timedelta(minutes=15)

        m_command = mock.MagicMock()
        m_scheduler = mock.MagicMock()
        with mock.patch.dict(PluginRegistry.modules, {'CommandRegistry': m_command, 'SchedulerService': m_scheduler}):
            self.mapper._JSONRPCObjectMapper__gc()
            assert 'countdown_job' in obj_desc
            assert 'mark_for_deletion' in obj_desc
            assert m_command.sendEvent.called
            assert m_scheduler.getScheduler.return_value.add_date_job.called
            m_scheduler.reset_mock()
            m_command.reset_mock()

            # second run -> abort running scheduler
            del obj_desc['mark_for_deletion']
            self.mapper._JSONRPCObjectMapper__gc()
            assert 'countdown_job' in obj_desc
            assert 'mark_for_deletion' in obj_desc
            assert m_command.sendEvent.called
            assert m_scheduler.getScheduler.return_value.unschedule_job.called
            assert m_scheduler.getScheduler.return_value.add_date_job.called
            m_scheduler.reset_mock()
            m_command.reset_mock()

            # execute the deletion
            obj_desc['mark_for_deletion'] = datetime.datetime.now() - datetime.timedelta(seconds=15)
            self.mapper._JSONRPCObjectMapper__gc()
            assert m_command.sendEvent.called
            assert self.mapper._JSONRPCObjectMapper__get_ref(res["__jsonclass__"][1][1]) is None
            m_scheduler.reset_mock()
            m_command.reset_mock()

            # start over
            res = self.openObject('admin', 'session-uuid', 'object', 'cn=Frank Reich,ou=people,dc=example,dc=net')
            ref = res["__jsonclass__"][1][1]
            obj_desc = self.mapper._JSONRPCObjectMapper__get_ref(res["__jsonclass__"][1][1])

            obj_desc['last_interaction'] = datetime.datetime.now() - datetime.timedelta(minutes=15)
            self.mapper._JSONRPCObjectMapper__gc()
            m_scheduler.reset_mock()
            m_command.reset_mock()
            self.mapper.continueObjectEditing('admin', res["__jsonclass__"][1][1])
            assert m_scheduler.getScheduler.return_value.unschedule_job.called
            assert not m_scheduler.getScheduler.return_value.add_date_job.called
            assert m_command.sendEvent.called
