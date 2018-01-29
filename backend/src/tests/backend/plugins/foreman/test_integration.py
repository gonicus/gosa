# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import glob
import hmac
from json import loads, dumps

import os

import pytest
from unittest import TestCase, mock

from sqlalchemy import and_
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, HTTPError

from gosa.backend.objects import ObjectProxy
from gosa.backend.objects.index import ObjectInfoIndex, KeyValueIndex
from gosa.common.components import PluginRegistry
from gosa.common.env import make_session
from tests.RemoteTestCase import RemoteTestCase
from gosa.backend.plugins.webhook.registry import WebhookReceiver
from tests.GosaTestCase import GosaTestCase
from gosa.backend.plugins.foreman.main import Foreman as ForemanPlugin
from gosa.backend.objects.backend.back_foreman import *
from gosa.backend.objects.backend.registry import ObjectBackendRegistry


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.cookies = {}
        self.url = None

    @property
    def content(self):
        return self.json()

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
    conditional_responses = {}
    triggers = {}

    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
        self.log = logging.getLogger(__name__)

        # read in all data
        for file in glob.glob("%s/**/*.json"):
            print("FILE: %s" % file[len(self.base_dir):])

    def __respond(self, path, method):
        rel = path[path.index("/api/")+5:]

        if rel[0:3] == "v2/":
            rel = rel[3:]
        resp_id = "%s|%s" % (path, method)
        use_file = True
        if resp_id in self.conditional_responses:
            logging.getLogger("test.foreman-integration").info("checking conditional responses")
            use_file = False
            for entry in self.conditional_responses[resp_id]:
                if entry[0]() is True:
                    return MockResponse(entry[1], 200)
                else:
                    logging.getLogger("test.foreman-integration").info("condition failed")

        if use_file:
            logging.getLogger("test.foreman-integration").info("checking file responses")
            file = os.path.join(self.base_dir, "%s.json" % rel)
            if os.path.exists(file):
                with open(file) as f:
                    return MockResponse(f.read(), 200)

        return MockResponse({}, 404)

    def get(self, url, **kwargs):
        logging.getLogger("test.foreman-integration").info("GET: %s" % url)
        return self.__respond(url, "get")

    def post(self, url, **kwargs):
        logging.getLogger("test.foreman-integration").info("POST: %s" % url)
        return MockResponse({}, 200)

    def put(self, url, **kwargs):
        tid = "%s|put" % url
        if tid in self.triggers:
            for trigger in self.triggers[tid]:
                if trigger['active'] is True:
                    trigger['cb'](**kwargs)
                elif trigger['act_cb'](**kwargs) is True:
                    trigger['active'] = True
                    trigger['cb'](**kwargs)
                else:
                    logging.getLogger("test.foreman-integration").info("inactive trigger")

        logging.getLogger("test.foreman-integration").info("PUT: %s (%s)" % (url, kwargs))
        return MockResponse({}, 200)

    def delete(self, url, **kwargs):
        logging.getLogger("test.foreman-integration").info("DELETE: %s" % url)
        return MockResponse({}, 200)

    def register_conditional_response(self, url, method, condition_callback, response):
        id = "%s|%s" % (url, method)
        if id not in self.conditional_responses:
            self.conditional_responses[id] = []
        self.conditional_responses[id].append((condition_callback, response))

        logging.getLogger("test.foreman-integration").info("conditional callback registered: %s" % id)

    def register_trigger(self, url, method, activation_callback, callback):
        tid = "%s|%s" % (url, method)
        if tid not in self.triggers:
            self.triggers[tid] = []
        self.triggers[tid].append({
            "active": False,
            "act_cb": activation_callback,
            "cb": callback
        })
        logging.getLogger("test.foreman-integration").info("trigger registered: %s" % id)


@mock.patch("gosa.backend.objects.backend.back_foreman.requests.post")
@mock.patch("gosa.backend.objects.backend.back_foreman.requests.put")
@mock.patch("gosa.backend.objects.backend.back_foreman.requests.delete")
@mock.patch("gosa.backend.objects.backend.back_foreman.requests.get")
class ForemanIntegrationTestCase(GosaTestCase, RemoteTestCase):
    foreman = None
    host_url = None
    host_token = None
    hook_url = None
    hook_token = None
    registry = None
    foreman_backend = None
    foreman_backend_client_backup = None

    def setUp(self):
        logging.getLogger("gosa.backend.plugins.foreman").setLevel(logging.DEBUG)
        # logging.getLogger("gosa.backend.objects").setLevel(logging.DEBUG)
        logging.getLogger("gosa.backend.objects").info("SET UP")
        super(ForemanIntegrationTestCase, self).setUp()
        env = Environment.getInstance()
        env.config.set("foreman.host-rdn", None)
        env.config.set("foreman.group-rdn", None)
        env.config.set("foreman.initial-sync", "false")
        self.foreman = ForemanPlugin()
        # just use a fake url as the requests are mocked anyway
        self.foreman.serve()
        self.foreman.create_container()
        self.registry = PluginRegistry.getInstance("WebhookRegistry")
        self.host_url, self.host_token = self.registry.registerWebhook("admin", "foreman-sp", "application/vnd.foreman.hostevent+json")
        self.hook_url, self.hook_token = self.registry.registerWebhook("admin", "foreman-hook", "application/vnd.foreman.hookevent+json")

        # add client with foreman connection tp backend
        self.foreman_backend = ObjectBackendRegistry.getBackend("Foreman")
        self.foreman_backend_client_backup = self.foreman_backend.client
        self.foreman_backend.client = ForemanClient(url="http://localhost:8000/api/v2")

    def tearDown(self):
        self.registry.unregisterWebhook("admin", "foreman-sp", "application/vnd.foreman.hostevent+json")
        self.registry.unregisterWebhook("admin", "foreman-hook", "application/vnd.foreman.hookevent+json")
        self.foreman_backend.client = self.foreman_backend_client_backup
        logging.getLogger("gosa.backend.plugins.foreman").setLevel(logging.INFO)
        # logging.getLogger("gosa.backend.objects").setLevel(logging.INFO)
        logging.getLogger("gosa.backend.objects").info("tear down")
        super(ForemanIntegrationTestCase, self).tearDown()

    def get_app(self):
        return Application([('/hooks(?P<path>.*)?', WebhookReceiver)], cookie_secret='TecloigJink4', xsrf_cookies=True)

    def test_provision_host(self, m_get, m_del, m_put, m_post):
        """ convert a discovered host to a 'real' host  """
        self._create_test_data()
        container = ObjectProxy(self._test_dn, "IncomingDeviceContainer")
        container.commit()

        mocked_foreman = MockForeman()
        m_get.side_effect = mocked_foreman.get
        m_del.side_effect = mocked_foreman.delete
        m_put.side_effect = mocked_foreman.put
        m_post.side_effect = mocked_foreman.post

        # create the discovered host + foremanHostgroup
        d_host = ObjectProxy(container.dn, "Device")
        d_host.cn = "mac00262df16a2c"
        d_host.extend("ForemanHost")
        d_host.status = "discovered"
        d_host.extend("ieee802Device")
        d_host.macAddress = "00:26:2d:f1:6a:2c"
        d_host.extend("IpHost")
        d_host.ipHostNumber = "192.168.0.1"
        d_host.commit()

        hostgroup = ObjectProxy("%s" % self._test_dn, "GroupOfNames")
        hostgroup.extend("ForemanHostGroup")
        hostgroup.cn = "Test"
        hostgroup.foremanGroupId = "4"
        hostgroup.commit()

        # add host to group
        logging.getLogger("test.foreman-integration").info("########### START: Add Host to group #############")
        d_host = ObjectProxy("cn=mac00262df16a2c,%s" % container.dn)

        def check():
            logging.getLogger("test.foreman-integration").info("check condition: %s, %s" % (d_host.cn, d_host.status))
            return d_host.cn == "mac00262df16a2c" and d_host.status == "discovered"

        def check2():
            logging.getLogger("test.foreman-integration").info("check2 condition: %s" % d_host.cn)
            return d_host.cn == "Testhost"

        base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
        with open(os.path.join(base_dir, "discovered_hosts", "mac00262df16a2c.json")) as f:
            mocked_foreman.register_conditional_response("http://localhost:8000/api/v2/discovered_hosts/mac00262df16a2c",
                                                         "get",
                                                         check,
                                                         f.read())
        with open(os.path.join(base_dir, "conditional", "Testhost.json")) as f:
            mocked_foreman.register_conditional_response("http://localhost:8000/api/v2/hosts/Testhost",
                                                         "get",
                                                         check2,
                                                         f.read())

        myself = self

        def activate(**kwargs):
            return True

        def execute(**kwargs):
            # execute realm request to GOsa
            payload = bytes(dumps({"parameters": {"update": "true", "userclass": "Test", "splat": [],
                                   "captures": ["GOSA"], "realm": "GOSA"}, "action": "create",
                                   "hostname": "Testhost"}), 'utf-8')

            signature_hash = hmac.new(bytes(myself.host_token, 'ascii'), msg=payload, digestmod="sha512")
            signature = 'sha1=' + signature_hash.hexdigest()
            headers = {
                'Content-Type': 'application/vnd.foreman.hostevent+json',
                'HTTP_X_HUB_SENDER': 'foreman-sp',
                'HTTP_X_HUB_SIGNATURE': signature
            }
            response = AsyncHTTPTestCase.fetch(myself, "/hooks/", method="POST", headers=headers, body=payload)
            assert response.code == 200

            # send update
            payload = bytes(dumps({
                "event": "after_commit",
                "object": "Testhost", 'data': {'host': {
                    'host': {'build': True, 'parameters': [], 'last_report': None, 'subnet_id': 1,
                             'name': 'Testhost', 'realm_name': 'GOSA', 'mac': '00:26:2d:f1:6a:2c'}}}}), 'utf-8')
            signature_hash = hmac.new(bytes(myself.hook_token, 'ascii'), msg=payload, digestmod="sha512")
            signature = 'sha1=' + signature_hash.hexdigest()
            headers = {
                'Content-Type': 'application/vnd.foreman.hookevent+json',
                'HTTP_X_HUB_SENDER': 'foreman-hook',
                'HTTP_X_HUB_SIGNATURE': signature
            }
            response = AsyncHTTPTestCase.fetch(myself, "/hooks/", method="POST", headers=headers, body=payload)
            assert response.code == 200

        mocked_foreman.register_trigger("http://localhost:8000/api/v2/discovered_hosts/mac00262df16a2c",
                                        "put",
                                        activate,
                                        execute)

        with make_session() as session:
            assert session.query(ObjectInfoIndex.dn)\
                       .join(ObjectInfoIndex.properties)\
                       .filter(and_(KeyValueIndex.key == "cn", KeyValueIndex.value == "Testhost"))\
                       .count() == 0

        d_host.cn = "Testhost"
        d_host.groupMembership = hostgroup.dn
        d_host.commit()

        logging.getLogger("test.foreman-integration").info("########### END: Add Host to group #############")

        # now move the host to the final destination
        d_host = ObjectProxy("cn=Testhost,ou=incoming,%s" % self._test_dn)
        assert d_host.status != "discovered"
        assert d_host.name == "Testhost"
        assert d_host.is_extended_by("RegisteredDevice")
        assert len(d_host.userPassword[0]) > 0
        assert d_host.deviceUUID is not None

        with make_session() as session:
            assert session.query(ObjectInfoIndex.dn) \
                       .join(ObjectInfoIndex.properties) \
                       .filter(and_(KeyValueIndex.key == "cn", KeyValueIndex.value == "Testhost")) \
                       .count() == 1

        logging.getLogger("test.foreman-integration").info("########### START: moving host #############")
        d_host.move("%s" % self._test_dn)
        logging.getLogger("test.foreman-integration").info("########### END: moving host #############")

        # lets check if everything is fine in the database
        d_host = ObjectProxy("cn=Testhost,ou=devices,%s" % self._test_dn, read_only=True)
        assert d_host is not None
        assert d_host.status == "unknown"
        assert d_host.groupMembership == hostgroup.dn


