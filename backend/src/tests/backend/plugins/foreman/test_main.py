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

import os
import pytest
from unittest import TestCase, mock

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, HTTPError

from gosa.backend.objects import ObjectProxy
from gosa.common.components import PluginRegistry
from tests.RemoteTestCase import RemoteTestCase
from gosa.backend.exceptions import ProxyException
from gosa.backend.plugins.webhook.registry import WebhookReceiver
from tests.GosaTestCase import GosaTestCase
from gosa.backend.plugins.foreman.main import Foreman as ForemanPlugin
from gosa.backend.objects.backend.back_foreman import *
import ldap


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.cookies = {}

    def json(self):
        if isinstance(self.json_data, dict):
            return self.json_data
        else:
            return loads(self.json_data)

    @property
    def ok(self):
        return self.status_code == 200

    def raise_for_status(self):
        raise HTTPError(self.status_code)


class MockForeman:

    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
        self.log = logging.getLogger(__name__)

    def __respond(self, path):
        rel = path[path.index("/api/")+5:]
        if rel[0:3] == "v2/":
            rel = rel[3:]
        file = os.path.join(self.base_dir, "%s.json" % rel)
        print("requested: %s" % file)
        if os.path.exists(file):
            with open(file) as f:
                return MockResponse(f.read(), 200)

        return MockResponse({}, 404)

    def get(self, url, **kwargs):
        return self.__respond(url)

    def post(self, url, **kwargs):
        return MockResponse({}, 200)

    def put(self, url, **kwargs):
        return MockResponse({}, 200)

    def delete(self, url, **kwargs):
        return MockResponse({}, 200)


@mock.patch("gosa.backend.objects.backend.back_foreman.requests.post")
@mock.patch("gosa.backend.objects.backend.back_foreman.requests.put")
@mock.patch("gosa.backend.objects.backend.back_foreman.requests.delete")
@mock.patch("gosa.backend.objects.backend.back_foreman.requests.get")
class ForemanTestCase(GosaTestCase):
    foreman = None

    def setUp(self):
        logging.getLogger("gosa.backend.plugins.foreman").setLevel(logging.DEBUG)
        logging.getLogger("gosa.backend.objects").setLevel(logging.DEBUG)
        logging.getLogger("gosa.backend.objects").info("SET UP")
        super(ForemanTestCase, self).setUp()
        self.foreman = ForemanPlugin()
        # just use a fake url as the requests are mocked anyway
        self.foreman.init_client("http://localhost:8000/api/v2")
        self.foreman.serve()
        self.foreman.create_container()

    def tearDown(self):
        logging.getLogger("gosa.backend.plugins.foreman").setLevel(logging.INFO)
        logging.getLogger("gosa.backend.objects").setLevel(logging.INFO)
        logging.getLogger("gosa.backend.objects").info("tear down")
        super(ForemanTestCase, self).tearDown()

    def test_add_host(self, m_get, m_del, m_put, m_post):
        self._create_test_data()

        m_get.return_value = MockResponse({
            "status": 0,
            "status_label": "Build"
        }, 200)

        logging.getLogger("gosa.backend.objects.index").setLevel(logging.DEBUG)
        key = self.foreman.add_host("testhost", base=self._test_dn)
        
        device = ObjectProxy("cn=testhost,ou=devices,%s" % self._test_dn)
        assert device.dn == "cn=testhost,ou=devices,%s" % self._test_dn
        assert device.cn == "testhost"
        assert device.userPassword[0:6] == "{SSHA}"

        m_del.return_value = MockResponse('{}', 200)
        
        device.remove()

    def test_remove_type(self, m_get, m_del, m_put, m_post):

        self._create_test_data()

        m_get.return_value = MockResponse({
            "status": 0,
            "status_label": "Build"
        }, 200)

        self.foreman.add_host("testhost", base=self._test_dn)

        device = ObjectProxy("cn=testhost,ou=devices,%s" % self._test_dn)
        dn = device.dn

        m_del.return_value = MockResponse('{}', 200)
        self.foreman.remove_type("ForemanHost", device.cn)

        with pytest.raises(ProxyException):
            ObjectProxy(dn)

    def test_update_type(self, m_get, m_del, m_put, m_post):
        self._create_test_data()
        self.foreman.client = ForemanClient()

        m_get.return_value = MockResponse({
            "name": "testhost"
        }, 200)
        self.foreman.add_host("testhost", base=self._test_dn)

        device = ObjectProxy("cn=testhost,ou=devices,%s" % self._test_dn)
        dn = device.dn

        assert device.cn == "testhost"
        assert device.ip is None

        data = {
            "name": "testhost",
            "ip": "192.168.0.3",
            "global_status": 0,
            "build_status": 1
        }
        m_get.return_value = MockResponse(data, 200)

        logging.getLogger("gosa.backend.objects").info("------------------------START UPDATING TYPE---------------------------------------")

        self.foreman.update_type("ForemanHost", device, data)

        # opening the object calls the mocked m_get method
        device = ObjectProxy(dn)
        assert device.ipHostNumber == "192.168.0.3"
        assert device.status == "pending"


@mock.patch("gosa.backend.objects.backend.back_foreman.requests.post")
@mock.patch("gosa.backend.objects.backend.back_foreman.requests.put")
@mock.patch("gosa.backend.objects.backend.back_foreman.requests.delete")
@mock.patch("gosa.backend.objects.backend.back_foreman.requests.get")
class ForemanSyncTestCase(GosaTestCase):

    dns_to_delete = []
    foreman = None
    log = None

    def setUp(self):
        self.log = logging.getLogger(__name__)
        logging.getLogger("gosa.backend.plugins.foreman").setLevel(logging.DEBUG)
        logging.getLogger("gosa.backend.objects").setLevel(logging.DEBUG)
        super(ForemanSyncTestCase, self).setUp()
        self.foreman = ForemanPlugin()
        self.foreman.serve()
        # just use a fake url as the requests are mocked anyway
        self.foreman.client = ForemanClient("http://localhost:8000/api/v2")
        self.foreman.create_container()

    def tearDown(self):
        # remove them all
        with mock.patch("gosa.backend.objects.backend.back_foreman.requests.delete") as m_del:
            m_del.return_value = MockResponse({}, 200)

            for dn in self.dns_to_delete:
                try:
                    self.log.info("deleting dn: %s" % dn)
                    obj = ObjectProxy(dn)
                    obj.remove()
                except Exception as e:
                    self.log.error("%s" % e)
                    pass

        logging.getLogger("gosa.backend.plugins.foreman").setLevel(logging.INFO)
        logging.getLogger("gosa.backend.objects").setLevel(logging.INFO)
        super(ForemanSyncTestCase, self).tearDown()

    def test_sync_type(self, m_get, m_del, m_put, m_post):
        mocked_foreman = MockForeman()
        m_get.side_effect = mocked_foreman.get
        m_del.side_effect = mocked_foreman.delete
        m_put.side_effect = mocked_foreman.put
        m_post.side_effect = mocked_foreman.post

        # check that there are not Objects yet
        index = PluginRegistry.getInstance("ObjectIndex")
        host_query = {
            '_type': 'Device',
            'cn': {
                'in_': ['smitty.intranet.gonicus.de', 'gosa.test.intranet.gonicus.de']
            },
            'extension': 'ForemanHost'
        }
        hostgroup_query = {
            '_type': 'ForemanHostGroup',
            'cn': {
                'in_': ['Bereitstellen von smitty.intranet.gonicus.de', 'VM', 'Test']
            },
        }
        discovered_host_query = {
            '_type': 'Device',
            'extension': 'ForemanHost',
            'status': 'discovered'
        }
        res = index.search(host_query, {'dn': 1})
        assert len(res) == 0
        res = index.search(hostgroup_query, {'dn': 1})
        assert len(res) == 0
        res = index.search(discovered_host_query, {'dn': 1})
        assert len(res) == 0

        self.foreman.sync_type("ForemanHostGroup")
        logging.getLogger("gosa.backend.objects.index").info("waiting for index update")
        logging.getLogger("gosa.backend.objects.index").info("checking index")
        res = index.search(host_query, {'dn': 1})
        assert len(res) == 0
        res = index.search(hostgroup_query, {'dn': 1})
        assert len(res) == 3
        res = index.search(discovered_host_query, {'dn': 1})
        assert len(res) == 0

        self.foreman.sync_type("ForemanHost")
        res = index.search(host_query, {'dn': 1})
        assert len(res) == 2
        res = index.search(hostgroup_query, {'dn': 1})
        assert len(res) == 3
        res = index.search(discovered_host_query, {'dn': 1})
        assert len(res) == 0

        self.foreman.sync_type("ForemanHost", "discovered_hosts")
        res = index.search(host_query, {'dn': 1})
        assert len(res) == 3
        self.dns_to_delete = [x['dn'] for x in res]

        res = index.search(hostgroup_query, {'dn': 1})
        assert len(res) == 3
        self.dns_to_delete += [x['dn'] for x in res]

        res = index.search(discovered_host_query, {'dn': 1})
        assert len(res) == 1
        self.dns_to_delete += [x['dn'] for x in res]


class ForemanClientTestCase(TestCase):

    @mock.patch("gosa.backend.objects.backend.back_foreman.requests.get")
    def test_get(self, m_get):
        client = ForemanClient("http://localhost:8000/api/v2")

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

    @mock.patch("gosa.backend.objects.backend.back_foreman.requests.get")
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

        otp_response = loads(response.body.decode("utf-8"))
        assert "randompassword" in otp_response
        assert otp_response["randompassword"] is not None

        # check if the host has been created
        device = ObjectProxy("cn=new-foreman-host,ou=incoming,dc=example,dc=net")
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
            ObjectProxy("cn=new-foreman-host,ou=incoming,dc=example,dc=net")


class ForemanHookTestCase(RemoteTestCase):
    registry = None
    url = None
    token = None
    _host_cn = None

    def setUp(self):
        super(ForemanHookTestCase, self).setUp()
        self.registry = PluginRegistry.getInstance("WebhookRegistry")
        self.url, self.token = self.registry.registerWebhook("admin", "test-webhook", "application/vnd.foreman.hookevent+json")

    def tearDown(self):
        super(ForemanHookTestCase, self).tearDown()
        self.registry.unregisterWebhook("admin", "test-webhook", "application/vnd.foreman.hookevent+json")

        if self._host_cn is not None:
            # cleanup
            foreman = ForemanPlugin()
            foreman.serve()
            foreman.remove_type("ForemanHost", self._host_cn)

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

    @mock.patch("gosa.backend.objects.backend.back_foreman.requests.get")
    def test_host_request(self, m_get):

        m_get.return_value = MockResponse('{\
            "build_status": 0\
        }', 200)

        host_dn = "cn=new-foreman-host,ou=incoming,dc=example,dc=net"
        self._host_cn = "new-foreman-host"
        # create new host to update
        foreman = ForemanPlugin()
        foreman.serve()
        foreman.add_host("new-foreman-host")

        payload_data = {
            "event": "after_commit",
            "object": "new-foreman-host",
            "data": {
                "host": {
                    "host": {
                        "name": "new-foreman-host",
                        "ip": "127.0.0.1",
                        "mac": "00:00:00:00:00:01",
                    }
                }
            }
        }

        headers, payload = self._create_request(payload_data)
        AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)

        # check if the host has been updated
        device = ObjectProxy(host_dn)
        assert device.cn == "new-foreman-host"
        assert device.ipHostNumber == payload_data["data"]["host"]["host"]["ip"]
        assert device.macAddress == payload_data["data"]["host"]["host"]["mac"]

        # delete the host
        payload_data = {
            "event": "after_destroy",
            "object": "new-foreman-host",
            "data": {
                "host": {
                    "host": {
                        "name": "new-foreman-host"
                    }
                }
            }
        }
        headers, payload = self._create_request(payload_data)
        AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)

        with pytest.raises(ProxyException):
            ObjectProxy("cn=new-foreman-host,ou=incoming,dc=example,dc=net")

        self._host_cn = None

    @mock.patch("gosa.backend.objects.backend.back_foreman.requests.delete")
    @mock.patch("gosa.backend.objects.backend.back_foreman.requests.get")
    def test_hostgroup_request(self, m_get, m_delete):

        m_get.return_value = MockResponse('{\
            "name": "Testgroup", \
            "id": 999\
        }', 200)

        self._host_dn = "cn=Testgroup,ou=groups,dc=example,dc=net"

        payload_data = {
            "event": "after_create",
            "object": "Testgroup",
            "data": {
                "hostgroup": {
                    "hostgroup": {
                        "id": 999,
                        "name": "Testgroup"
                    }
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
                    "hostgroup": {
                        "id": 999,
                        "name": "Testgroup"
                    }
                }
            }
        }
        headers, payload = self._create_request(payload_data)
        AsyncHTTPTestCase.fetch(self, "/hooks/", method="POST", headers=headers, body=payload)

        with pytest.raises(ldap.NO_SUCH_OBJECT):
            ObjectProxy(self._host_dn)

        self._host_dn = None

