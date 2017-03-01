# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import TestCase, mock
from gosa.backend.plugins.user.main import User
from gosa.common import Environment


class UserMainTestCase(TestCase):

    def test_generateUid(self):
        user = TestUser()
        assert user is not None

        env = Environment.getInstance().config

        # enable test when using gosa's transliterate
        with mock.patch.object(env, 'get') as mock_config:
            mock_config.return_value = '{%sn}'
            assert user.generateUid({'sn': 'SmÜrübröd'}) == ['SmUeruebroed']

            mock_config.return_value = '{%prename} {%sn}'
            assert user.generateUid({'prename': 'Владимир', 'sn': 'Путин'}) == ['Vladimir Putin']

            mock_config.return_value = '{%sn}'
            assert user.generateUid({'sn': 'Doe'}) == ['Doe']
            assert user.generateUid({'sn': 'Dorian'}) == ['Dorian']
            mock_config.return_value = '{%sn}-{%prename}'
            assert user.generateUid({'sn': 'Doe', 'prename': 'John'}) == ['Doe-John']

            mock_config.return_value = '{%sn[1]}'
            assert user.generateUid({'sn': 'Doe'}) == ['o']
            mock_config.return_value = '{%sn[1-3]}'
            assert user.generateUid({'sn': 'Dorian'}) == ['o', 'or']
            mock_config.return_value = '{%prename}-{%sn[1-3]}'
            assert user.generateUid({'sn': 'Dorian', 'prename': 'John'}) == ['John-o', 'John-or']
            mock_config.return_value = '{%prename[1-3]}-{%sn[1-3]}'
            assert user.generateUid({'sn': 'Dorian', 'prename': 'John'}) == ['o-o', 'o-or', 'oh-o', 'oh-or']

            mock_config.return_value = '{%Sn}'
            assert user.generateUid({'Sn': 'Doe'}) == ['Doe']

            mock_config.return_value = '{%sn}-{id:3}'
            assert user.generateUid({'sn': 'doe'}) == ['doe-000']
            user.existing_uids = ['doe-000', 'doe-001', 'doe-002']
            mock_config.return_value = '{%sn}-{id:3}'
            assert user.generateUid({'sn': 'doe'}) == ['doe-003']
            mock_config.return_value = '{%sn[0-3]}-{id:3}'
            assert user.generateUid({'sn': 'doe'}) == ['d-000', 'do-000', 'doe-003']

            mock_config.return_value = '{id#3}'
            random_id = user.generateUid(None)[0]
            assert len(random_id) == 3
            assert int(random_id) >= 100
            assert int(random_id) < 1000

            mock_config.return_value = '{%sn}{id!2}'
            user.existing_uids = []
            assert user.generateUid({'sn': 'doe'}) == ['doe']
            user.existing_uids = ['doe']
            assert user.generateUid({'sn': 'doe'}) == ['doe01']
            user.existing_uids = ['doe', 'doe01']
            assert user.generateUid({'sn': 'doe'}) == ['doe02']
            user.existing_uids = ['doe01']
            assert user.generateUid({'sn': 'doe'}) == ['doe']

            mock_config.return_value = '{%sn}'
            user.existing_uids = ['doe']
            assert user.generateUid({'sn': 'doe'}) == []


class TestUser(User):

    existing_uids = []

    def uid_exists(self, uid):
        return uid in self.existing_uids
