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
from tornado.web import Application, HTTPError

from tests.RemoteTestCase import RemoteTestCase
from gosa.backend.exceptions import ProxyException
from gosa.backend.plugins.webhook.registry import WebhookReceiver
from tests.GosaTestCase import GosaTestCase
from gosa.backend.plugins.foreman.main import *
import ldap


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return loads(self.json_data)

    @property
    def ok(self):
        return self.status_code == 200

    def raise_for_status(self):
        raise HTTPError(self.status_code)


@mock.patch("gosa.backend.plugins.foreman.main.requests.get")
class ForemanTestCase(GosaTestCase):

    def tearDown(self):
        logging.getLogger("gosa.backend.objects.index").setLevel(logging.INFO)
        super(ForemanTestCase, self).tearDown()

    def test_add_host(self, m_get):
        self._create_test_data()
        foreman = Foreman()
        foreman.serve()

        m_get.return_value = MockResponse('{\
            "status": 0,\
            "status_label": "Build"\
        }', 200)

        logging.getLogger("gosa.backend.objects.index").setLevel(logging.DEBUG)
        key = foreman.add_host("testhost", base=self._test_dn)
        
        device = ObjectProxy("cn=testhost,ou=devices,%s" % self._test_dn)
        assert device.dn == "cn=testhost,ou=devices,%s" % self._test_dn
        assert device.cn == "testhost"
        assert device.userPassword[0:6] == "{SSHA}"
        
        device.remove()

    def test_remove_host(self, m_get):

        self._create_test_data()
        foreman = Foreman()
        foreman.serve()

        m_get.return_value = MockResponse('{\
            "status": 0,\
            "status_label": "Build"\
        }', 200)

        foreman.add_host("testhost", base=self._test_dn)

        device = ObjectProxy("cn=testhost,ou=devices,%s" % self._test_dn)
        dn = device.dn

        foreman.remove_host(device.cn)

        with pytest.raises(ProxyException):
            ObjectProxy(dn)

    def test_update_host(self, m_get):
        self._create_test_data()
        foreman = Foreman()
        foreman.client = ForemanClient()
        foreman.serve()

        m_get.return_value = MockResponse('{\
            "status": 0,\
            "status_label": "Build"\
        }', 200)

        foreman.add_host("testhost", base=self._test_dn)

        device = ObjectProxy("cn=testhost,ou=devices,%s" % self._test_dn)
        dn = device.dn

        assert device.cn == "testhost"

        m_get.return_value = MockResponse('{\
            "name": "testhost",\
            "ip": "192.168.0.2",\
            "global_status": 0,\
            "build_status": 1\
        }', 200)

        foreman.update_host(device.cn)

        device = ObjectProxy(dn)
        assert device.ipHostNumber == "192.168.0.2"
        assert device.status == "pending"


class ForemanClientTestCase(TestCase):

    @mock.patch("gosa.backend.plugins.foreman.main.requests.get")
    def test_get(self, m_get):
        client = ForemanClient()

        m_get.return_value = MockResponse({}, 404)
        with pytest.raises(HTTPError):
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


class ForemanRealmTestCase(RemoteTestCase):
    registry = None
    url = None
    token = None

    def setUp(self):
        super(ForemanRealmTestCase, self).setUp()
        self.registry = PluginRegistry.getInstance("WebhookRegistry")
        self.url, self.token = self.registry.registerWebhook("admin", "test-webhook", "application/vnd.foreman.hostevent+json")

    def tearDown(self):
        super(ForemanRealmTestCase, self).tearDown()
        self.registry.unregisterWebhook("admin", "test-webhook", "application/vnd.foreman.hostevent+json")

    def get_app(self):
        return Application([('/hooks(?P<path>.*)?', WebhookReceiver)], cookie_secret='TecloigJink4', xsrf_cookies=True)

    @mock.patch("gosa.backend.plugins.foreman.main.requests.get")
    def test_request(self, m_get):

        m_get.return_value = MockResponse('{\
            "status": 0,\
            "status_label": "Build"\
        }', 200)

        token = bytes(self.token, 'ascii')
        payload = bytes(dumps({
            "action": "create",
            "hostname": "new-foreman-host",
            "parameters": {}
        }), 'utf-8')
        signature_hash = hmac.new(token, msg=payload, digestmod="sha512")
        signature = 'sha1=' + signature_hash.hexdigest()
        headers = {
            'Content-Type': 'application/vnd.foreman.hostevent+json',
            'HTTP_X_HUB_SENDER': 'test-webhook',
            'HTTP_X_HUB_SIGNATURE': signature
        }
        response = AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)

        otp_response = loads(response.body)
        assert "randompassword" in otp_response
        assert otp_response["randompassword"] is not None

        # check if the host has been created
        device = ObjectProxy("cn=new-foreman-host,ou=devices,dc=example,dc=net")
        assert device.cn == "new-foreman-host"

        # delete the host
        payload = bytes(dumps({
            "action": "delete",
            "hostname": "new-foreman-host",
            "parameters": {}
        }), 'utf-8')
        signature_hash = hmac.new(token, msg=payload, digestmod="sha512")
        signature = 'sha1=' + signature_hash.hexdigest()
        headers['HTTP_X_HUB_SIGNATURE'] = signature
        AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)

        with pytest.raises(ProxyException):
            ObjectProxy("cn=new-foreman-host,ou=devices,dc=example,dc=net")


class ForemanHookTestCase(RemoteTestCase):
    registry = None
    url = None
    token = None
    _host_dn = None

    def setUp(self):
        super(ForemanHookTestCase, self).setUp()
        self.registry = PluginRegistry.getInstance("WebhookRegistry")
        self.url, self.token = self.registry.registerWebhook("admin", "test-webhook", "application/vnd.foreman.hookevent+json")

    def tearDown(self):
        super(ForemanHookTestCase, self).tearDown()
        self.registry.unregisterWebhook("admin", "test-webhook", "application/vnd.foreman.hookevent+json")

        if self._host_dn is not None:
            # cleanup
            foreman = Foreman()
            foreman.server()
            foreman.remove_host(self._host_dn)

    def get_app(self):
        return Application([('/hooks(?P<path>.*)?', WebhookReceiver)], cookie_secret='TecloigJink4', xsrf_cookies=True)

    def _create_request(self, payload_data):
        token = bytes(self.token, 'ascii')
        payload = bytes(dumps(payload_data), 'utf-8')
        signature_hash = hmac.new(token, msg=payload, digestmod="sha512")
        signature = 'sha1=' + signature_hash.hexdigest()
        headers = {
            'Content-Type': 'application/vnd.foreman.hookevent+json',
            'HTTP_X_HUB_SENDER': 'test-webhook',
            'HTTP_X_HUB_SIGNATURE': signature
        }
        return headers, payload

    @mock.patch("gosa.backend.plugins.foreman.main.requests.get")
    def test_host_request(self, m_get):

        m_get.return_value = MockResponse('{\
            "build_status": 0\
        }', 200)

        self._host_dn = "cn=new-foreman-host,ou=devices,dc=example,dc=net"
        # create new host to update
        foreman = Foreman()
        foreman.serve()
        foreman.add_host("new-foreman-host")

        payload_data = {
            "event": "after_commit",
            "object": "new-foreman-host",
            "data": {
                "host": {
                    "ip": "127.0.0.1",
                    "mac": "00:00:00:00:00:01",
                    "uuid": "597ae2f6-16a6-1027-98f4-d28b5365dc14"
                }
            }
        }
        headers, payload = self._create_request(payload_data)
        AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)

        # check if the host has been updated
        device = ObjectProxy(self._host_dn)
        assert device.cn == "new-foreman-host"
        assert device.ipHostNumber == payload_data["data"]["host"]["ip"]
        assert device.macAddress == payload_data["data"]["host"]["mac"]
        assert device.deviceUUID == payload_data["data"]["host"]["uuid"]

        # delete the host
        payload_data = {
            "event": "after_destroy",
            "object": "new-foreman-host",
            "data": {"host": {
                "name": "new-foreman-host"
            }}
        }
        headers, payload = self._create_request(payload_data)
        AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)

        with pytest.raises(ProxyException):
            ObjectProxy("cn=new-foreman-host,ou=devices,dc=example,dc=net")

        self._host_dn = None

    @mock.patch("gosa.backend.plugins.foreman.main.requests.get")
    def test_hostgroup_request(self, m_get):

        m_get.return_value = MockResponse('{\
            "name": "Testgroup"\
        }', 200)

        self._host_dn = "cn=Testgroup,ou=groups,dc=example,dc=net"

        payload_data = {
            "event": "after_create",
            "object": "Testgroup",
            "data": {
                "hostgroup": {
                    "id": "999",
                    "name": "Testgroup"
                }
            }
        }
        headers, payload = self._create_request(payload_data)
        AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)

        # check if the host has been updated
        device = ObjectProxy(self._host_dn)
        assert device.cn == "Testgroup"
        assert device.foremanGroupId == "999"

        # delete the host
        payload_data = {
            "event": "after_destroy",
            "object": "Testgroup",
            "data": {
                "hostgroup": {
                    "id": "999",
                    "name": "Testgroup"
                }
            }
        }
        headers, payload = self._create_request(payload_data)
        AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)

        with pytest.raises(ldap.NO_SUCH_OBJECT):
            ObjectProxy(self._host_dn)

        self._host_dn = None

