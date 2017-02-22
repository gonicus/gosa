# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from datetime import datetime
from lxml import etree
from unittest import mock

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application
from tests.RemoteTestCase import RemoteTestCase
from gosa.backend.plugins.webhook.registry import *
from gosa.common.event import EventMaker


class TestWebhook(object):
    type = "Test"

    def handle_request(self, request_handler):
        self.content(request_handler.request.body)

    def content(self, content):
        pass


class WebhookEventReceiverTestCase(RemoteTestCase):

    def get_app(self):
        return Application([('/hooks(?P<path>.*)?', WebhookReceiver)], cookie_secret='TecloigJink4', xsrf_cookies=True)

    def tearDown(self):
        super(WebhookEventReceiverTestCase, self).tearDown()
        registry = PluginRegistry.getInstance("WebhookRegistry")
        registry.unregisterWebhook("admin", "test-webhook", "application/vnd.gosa.test+plain")
        registry.unregister_handler("application/vnd.gosa.test+plain")

    def test_registering(self):
        registry = PluginRegistry.getInstance("WebhookRegistry")
        hook = TestWebhook()
        registry.register_handler("application/vnd.gosa.test+plain", hook)
        url, token = registry.registerWebhook("admin", "test-webhook", "application/vnd.gosa.test+plain")

        token = bytes(token, 'ascii')
        signature_hash = hmac.new(token, msg=b"Test", digestmod="sha512")
        signature = 'sha1=' + signature_hash.hexdigest()
        headers = {
            'Content-Type': 'application/vnd.gosa.test+plain',
            'HTTP_X_HUB_SENDER': 'test-webhook',
            'HTTP_X_HUB_SIGNATURE': signature
        }
        with mock.patch.object(hook, "content") as m_content:
            AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=b"Test")
            m_content.assert_called_with(b"Test")
            m_content.reset_mock()

            registry.unregisterWebhook("admin", "test-webhook", "application/vnd.gosa.test+plain")
            AsyncHTTPTestCase.fetch(self, url, method="POST", headers=headers, body=b"Test")
            assert not m_content.called

    def test_post(self):

        # create webhook post
        e = EventMaker()
        update = e.Event(
            e.BackendChange(
                e.DN("cn=Test,ou=people,dc=example,dc=net"),
                e.ModificationTime(datetime.now().strftime("%Y%m%d%H%M%SZ")),
                e.ChangeType("update")
            )
        )
        payload = etree.tostring(update)

        token = bytes(Environment.getInstance().config.get("webhooks.ldap_monitor_token"), 'ascii')
        signature_hash = hmac.new(token, msg=payload, digestmod="sha512")
        signature = 'sha1=' + signature_hash.hexdigest()

        headers = {
            'Content-Type': 'application/vnd.gosa.event+xml',
            'HTTP_X_HUB_SENDER': 'backend-monitor',
            'HTTP_X_HUB_SIGNATURE': signature
        }
        with mock.patch("gosa.backend.plugins.webhook.registry.zope.event.notify") as m_notify:
            AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)
            assert m_notify.called
            m_notify.reset_mock()

            # unregistered sender
            headers['HTTP_X_HUB_SENDER'] = 'unknown'
            resp = AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)
            assert resp.code == 401
            assert not m_notify.called

            # wrong signature
            headers['HTTP_X_HUB_SENDER'] = 'backend-monitor'
            headers['HTTP_X_HUB_SIGNATURE'] = 'sha1=823rjadfkjlasasddfdgasdfgasd'
            resp = AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)
            assert resp.code == 401
            assert not m_notify.called

            # no signature
            del headers['HTTP_X_HUB_SIGNATURE']
            resp = AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)
            assert resp.code == 401
            assert not m_notify.called

            # no handler for content type
            headers['HTTP_X_HUB_SIGNATURE'] = signature
            headers['Content-Type'] = 'application/vnd.gosa.unknown+xml'
            resp = AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)
            assert resp.code == 401
            assert not m_notify.called
