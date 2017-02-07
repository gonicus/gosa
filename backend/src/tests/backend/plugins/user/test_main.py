# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import TestCase
from gosa.backend.plugins.user.main import User


class UserMainTestCase(TestCase):

    def test_generateUid(self):
        user = TestUser()
        assert user is not None

        # enable test when using gosa's transliterate
        assert user.generateUid('{%sn}', {'sn': 'SmÜrübröd'}) == ['smueruebroed']
        assert user.generateUid('{%prename} {%sn}', {'prename': 'Владимир', 'sn': 'Путин'}) == ['vladimir putin']

        assert user.generateUid('{%sn}', {'sn': 'Doe'}) == ['doe']
        assert user.generateUid('{%sn}', {'sn': 'Dorian'}) == ['dorian']
        assert user.generateUid('{%sn}-{%prename}', {'sn': 'Doe', 'prename': 'John'}) == ['doe-john']

        assert user.generateUid('{%sn[1]}', {'sn': 'Doe'}) == ['o']
        assert user.generateUid('{%sn[1-3]}', {'sn': 'Dorian'}) == ['o', 'or']
        assert user.generateUid('{%prename}-{%sn[1-3]}', {'sn': 'Dorian', 'prename': 'John'}) == ['john-o', 'john-or']
        assert user.generateUid('{%prename[1-3]}-{%sn[1-3]}', {'sn': 'Dorian', 'prename': 'John'}) == ['o-o', 'o-or', 'oh-o', 'oh-or']

        assert user.generateUid('{%Sn}', {'sn': 'Doe'}) == ['doe']

        assert user.generateUid('{%sn}-{id:3}', {'sn': 'Doe'}) == ['doe-000']
        user.existing_uids = ['doe-000', 'doe-001', 'doe-002']
        assert user.generateUid('{%sn}-{id:3}', {'sn': 'Doe'}) == ['doe-003']
        assert user.generateUid('{%sn[0-3]}-{id:3}', {'sn': 'Doe'}) == ['d-000', 'do-000', 'doe-003']

        random_id = user.generateUid('{id#3}', None)[0]
        assert len(random_id) == 3
        assert int(random_id) >= 100
        assert int(random_id) < 1000

        user.existing_uids = []
        assert user.generateUid('{%sn}{id!2}', {'sn': 'Doe'}) == ['doe']
        user.existing_uids = ['doe']
        assert user.generateUid('{%sn}{id!2}', {'sn': 'Doe'}) == ['doe01']
        user.existing_uids = ['doe', 'doe01']
        assert user.generateUid('{%sn}{id!2}', {'sn': 'Doe'}) == ['doe02']
        user.existing_uids = ['doe01']
        assert user.generateUid('{%sn}{id!2}', {'sn': 'Doe'}) == ['doe']

        user.existing_uids = ['doe']
        assert user.generateUid('{%sn}', {'sn': 'Doe'}) == []


class TestUser(User):

    existing_uids = []

    def uid_exists(self, uid):
        return uid in self.existing_uids
