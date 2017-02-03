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

    def test_generateId(self):
        user = User()
        assert user is not None

        # enable test when using gosa's transliterate
        assert user.generateId('{%sn}', {'sn': 'SmÜrübröd'}) == 'SmUeruebroed'
        assert user.generateId('{%prename} {%sn}', {'prename': 'Владимир', 'sn': 'Путин'}) == 'Vladimir Putin'

        assert user.generateId('{%sn}', {'sn': 'Doe'}) == 'Doe'
        assert user.generateId('{%sn}-{%prename}', {'sn': 'Doe', 'prename': 'John'}) == 'Doe-John'

        assert user.generateId('{%sn[1]}', {'sn': 'Doe'}) == 'o'
        assert user.generateId('{%sn[1-3]}', {'sn': 'Dorian'}) == 'or'

        assert user.generateId('{id:3}', None) == "001"

        random_id = user.generateId('{id#3}', None)
        assert len(random_id) == 3
        assert int(random_id) >= 100
        assert int(random_id) < 1000
