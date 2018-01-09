# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import mock
from urllib.parse import urlencode

from tornado.testing import AsyncHTTPTestCase
from gosa.backend.plugins.mqtt.mosquitto_auth import *
from tornado.web import Application


class MosquittoAuthTestCase(AsyncHTTPTestCase):

    def setUp(self):
        super(MosquittoAuthTestCase, self).setUp()
        self.env = Environment.getInstance()
        self.env.core_uuid = "fake_uuid"
        self.env.core_key = "fake_key"

    def tearDown(self):
        if hasattr(self.env, "core_key"):
            del self.env.core_key
        if hasattr(self.env, "core_uuid"):
            del self.env.core_uuid

    def get_app(self):
        return Application([
            ('/mqtt/auth', MosquittoAuthHandler),
            ('/mqtt/acl', MosquittoAclHandler),
            ('/mqtt/superuser', MosquittoSuperuserHandler)
        ])

    def test_auth(self):
        # normal user
        params = urlencode({'username': 'admin', 'password': 'tester'})
        response = self.fetch('/mqtt/auth', method="POST", body=params)
        assert response.code == 200

        # unknown user
        params = urlencode({'username': 'unknown', 'password': 'tester'})
        response = self.fetch('/mqtt/auth', method="POST", body=params)
        assert response.code == 403

        # backend
        params = urlencode({'username': self.env.core_uuid, 'password': self.env.core_key})
        response = self.fetch('/mqtt/auth', method="POST", body=params)
        assert response.code == 200

        # client without backend credentials set
        del self.env.core_key
        del self.env.core_uuid
        params = urlencode({'username': 'admin', 'password': 'tester'})
        response = self.fetch('/mqtt/auth', method="POST", body=params)
        assert response.code == 200

    def test_acl(self):
        # superuser is disabled
        params = urlencode({'username': 'superadmin', 'topic': 'test/topic'})
        response = self.fetch('/mqtt/superuser', method="POST", body=params)
        assert response.code == 403

        test_matrix = [
            {
                'topic': "%s/client/uuid" % self.env.domain,
                'username': self.env.core_uuid,
                'publish': True,
                'subscribe': True
            },
            {
                'topic': "%s/client/broadcast" % self.env.domain,
                'username': self.env.core_uuid,
                'publish': True,
                'subscribe': True
            },
            {
                'topic': "%s/client/uuid/request" % self.env.domain,
                'username': self.env.core_uuid,
                'publish': True,
                'subscribe': False
            },
            {
                'topic': "%s/client/uuid/response" % self.env.domain,
                'username': self.env.core_uuid,
                'publish': False,
                'subscribe': True
            },
            {
                'topic': "%s/events" % self.env.domain,
                'username': self.env.core_uuid,
                'publish': True,
                'subscribe': True
            },
            {
                'topic': "%s/unknown-topic" % self.env.domain,
                'username': self.env.core_uuid,
                'publish': False,
                'subscribe': False
            },
            {
                'topic': "%s/client/uuid" % self.env.domain,
                'username': 'uuid',
                'publish': True,
                'subscribe': True
            },
            {
                'topic': "%s/client/other_uuid" % self.env.domain,
                'username': 'uuid',
                'publish': False,
                'subscribe': False
            },
            {
                'topic': "%s/client/uuid/response" % self.env.domain,
                'username': 'uuid',
                'publish': True,
                'subscribe': False
            },
            {
                'topic': "%s/client/uuid/request" % self.env.domain,
                'username': 'uuid',
                'publish': False,
                'subscribe': True
            },
            {
                'topic': "%s/client/broadcast" % self.env.domain,
                'username': 'uuid',
                'publish': False,
                'subscribe': True
            }
        ]

        for test in test_matrix:
            for acc in ['publish', 'subscribe']:
                params = urlencode({'username': test['username'], 'topic': test['topic'], 'acc': 2 if acc == "publish" else 1})
                response = self.fetch('/mqtt/acl', method="POST", body=params)
                msg = "%s should %s to %s to topic %s" % (
                    "client" if test['username'] != self.env.core_uuid else "backend",
                    "not be allowed" if not test[acc] else "be allowed",
                    acc,
                    test['topic']
                )
                assert response.code == (200 if test[acc] else 403), msg

        # test event channel for client separately as we need to mock the acl check
        with mock.patch("gosa.backend.plugins.mqtt.mosquitto_auth.PluginRegistry.getInstance") as m_resolver:
            m_resolver.return_value.check.return_value = False
            params = urlencode({'username': 'uuid', 'topic': "%s/events" % self.env.domain, 'acc': 2})
            response = self.fetch('/mqtt/acl', method="POST", body=params)
            assert response.code == 403

            params = urlencode({'username': 'uuid', 'topic': "%s/events" % self.env.domain, 'acc': 1})
            response = self.fetch('/mqtt/acl', method="POST", body=params)
            assert response.code == 403

            m_resolver.return_value.check.return_value = True
            params = urlencode({'username': 'uuid', 'topic': "%s/events" % self.env.domain, 'acc': 2})
            response = self.fetch('/mqtt/acl', method="POST", body=params)
            assert response.code == 200

            params = urlencode({'username': 'uuid', 'topic': "%s/events" % self.env.domain, 'acc': 1})
            response = self.fetch('/mqtt/acl', method="POST", body=params)
            assert response.code == 200
