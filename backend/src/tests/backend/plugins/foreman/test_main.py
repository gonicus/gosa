# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import hmac
from json import loads, dumps

import pytest
from unittest import TestCase, mock

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

from gosa.common.utils import is_uuid
from tests.RemoteTestCase import RemoteTestCase
from gosa.backend.exceptions import ProxyException
from gosa.backend.plugins.webhook.registry import WebhookReceiver
from tests.GosaTestCase import GosaTestCase
from gosa.backend.plugins.foreman.main import *


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return loads(self.json_data)

    @property
    def ok(self):
        return self.status_code == 200


class ForemanTestCase(GosaTestCase):

    def test_addHost(self):
        self._create_test_data()
        foreman = Foreman()
        foreman.serve()

        with pytest.raises(ForemanException):
            # no mac
            foreman.addHost("admin", "testhost", params={}, base=self._test_dn)

        device = foreman.addHost("admin", "testhost", params={
            "mac": "00:00:00:00:00:01",
            "location_id": "loc1",
            "ip": "192.168.0.1",
            "owner_id": "1"
        }, base=self._test_dn)
        assert device.dn == "cn=testhost,ou=devices,%s" % self._test_dn
        assert device.macAddress == "00:00:00:00:00:01"
        assert device.l == "loc1"

    def test_removeHost(self):

        self._create_test_data()
        foreman = Foreman()
        foreman.serve()

        device = foreman.addHost("admin", "testhost", params={
            "mac": "00:00:00:00:00:01",
            "ip": "192.168.0.1",
            "location_id": "loc1",
            "owner_id": "1"
        }, base=self._test_dn)

        dn = device.dn

        foreman.removeHost("admin", device.cn)

        with pytest.raises(ProxyException):
            ObjectProxy(dn)

    @mock.patch("gosa.backend.plugins.foreman.main.requests.get")
    def test_update_host(self, m_get):
        self._create_test_data()
        foreman = Foreman()
        foreman.serve()

        m_get.return_value = MockResponse('{\
            "id": "testhost",\
            "ip": "192.168.0.2",\
            "location_id": "testloc1"\
        }', 200)

        device = foreman.addHost("admin", "testhost", params={
            "mac": "00:00:00:00:00:01",
            "location_id": "loc1",
            "ip": "192.168.0.1",
            "owner_id": "1"
        }, base=self._test_dn)

        dn = device.dn

        device = ObjectProxy(dn)
        assert device.l == "loc1"
        assert device.ipHostNumber == "192.168.0.1"

        foreman.update_host(device.cn)

        device = ObjectProxy(dn)
        assert device.l == "testloc1"
        assert device.ipHostNumber == "192.168.0.2"


class ForemanClientTestCase(TestCase):

    @mock.patch("gosa.backend.plugins.foreman.main.requests.get")
    def test_get(self, m_get):
        client = ForemanClient()

        m_get.return_value = MockResponse({}, 404)
        with pytest.raises(ForemanException):
            client.get("unknown")

        m_get.return_value = MockResponse('{\
            "total": 3,\
            "subtotal": 3,\
            "page": 1,\
            "per_page": 20,\
            "search": null,\
            "sort": {\
                "by": null,\
                "order": null\
            },\
            "results": [\
                {\
                    "id": 23,\
                    "name": "qa.lab.example.com",\
                    "fullname": "QA",\
                    "dns_id": 10,\
                    "created_at": "2013-08-13T09:02:31Z",\
                    "updated_at": "2013-08-13T09:02:31Z"\
                },\
                {\
                    "id": 25,\
                    "name": "sat.lab.example.com",\
                    "fullname": "SATLAB",\
                    "dns_id": 8,\
                    "created_at": "2013-08-13T08:32:48Z",\
                    "updated_at": "2013-08-14T07:04:03Z"\
                },\
                {\
                    "id": 32,\
                    "name": "hr.lab.example.com",\
                    "fullname": "HR",\
                    "dns_id": 8,\
                    "created_at": "2013-08-16T08:32:48Z",\
                    "updated_at": "2013-08-16T07:04:03Z"\
                }\
            ]\
        }', 200)

        res = client.get("domains")
        assert m_get.called_with("http://localhost/api/domains")
        assert res['total'] == 3
        assert len(res['results']) == res['total']

        m_get.return_value = MockResponse('{\
            "id": 23,\
            "name": "qa.lab.example.com",\
            "fullname": "QA",\
            "dns_id": 10,\
            "created_at": "2013-08-13T09:02:31Z",\
            "updated_at": "2013-08-13T09:02:31Z"\
        }', 200)

        res = client.get("domains", 23)
        assert m_get.called_with("http://localhost/api/domains/23")
        assert res['id'] == 23
        assert res['fullname'] == "QA"


class ForemanWebhookTestCase(RemoteTestCase):
    registry = None
    url = None
    token = None

    def setUp(self):
        super(ForemanWebhookTestCase, self).setUp()
        self.registry = PluginRegistry.getInstance("WebhookRegistry")
        self.url, self.token = self.registry.registerWebhook("admin", "test-webhook", "application/vnd.acme.hostevent+json")

    def tearDown(self):
        super(ForemanWebhookTestCase, self).tearDown()
        self.registry.unregisterWebhook("admin", "test-webhook", "application/vnd.acme.hostevent+json")

    def get_app(self):
        return Application([('/hooks(?P<path>.*)?', WebhookReceiver)], cookie_secret='TecloigJink4', xsrf_cookies=True)

    def test_request(self):

        token = bytes(self.token, 'ascii')
        payload = bytes(dumps({
            "action": "create",
            "hostname": "new-foreman-host",
            "parameters": {
                "mac": "00:00:00:00:00:01",
                "ip": "192.168.0.1"
            }
        }), 'utf-8')
        signature_hash = hmac.new(token, msg=payload, digestmod="sha512")
        signature = 'sha1=' + signature_hash.hexdigest()
        headers = {
            'Content-Type': 'application/vnd.acme.hostevent+json',
            'HTTP_X_HUB_SENDER': 'test-webhook',
            'HTTP_X_HUB_SIGNATURE': signature
        }
        response = AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)
        assert is_uuid(response.body.decode('utf-8'))

        # check if the host has been created
        device = ObjectProxy("cn=new-foreman-host,ou=devices,dc=example,dc=net")
        assert device.macAddress == "00:00:00:00:00:01"

        # delete the host
        payload = bytes(dumps({
            "action": "delete",
            "hostname": "new-foreman-host",
            "parameters": {
                "mac": "00:00:00:00:00:01"
            }
        }), 'utf-8')
        signature_hash = hmac.new(token, msg=payload, digestmod="sha512")
        signature = 'sha1=' + signature_hash.hexdigest()
        headers['HTTP_X_HUB_SIGNATURE'] = signature
        AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)
        with pytest.raises(ProxyException):
            ObjectProxy("cn=new-foreman-host,ou=devices,dc=example,dc=net")

