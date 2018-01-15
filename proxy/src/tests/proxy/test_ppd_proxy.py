import shutil
import os
from gosa.proxy.ppd_proxy import PPDProxy
from unittest import TestCase, mock


class PPDProxyTestCase(TestCase):

    def setUp(self):
        super(PPDProxyTestCase, self).setUp()
        self.proxy = PPDProxy()

    def tearDown(self):
        shutil.rmtree(self.proxy.ppd_dir)
        super(PPDProxyTestCase, self).tearDown()

    def test_getPPDURL(self):
        with mock.patch("gosa.proxy.ppd_proxy.make_session") as m,\
                mock.patch("gosa.proxy.ppd_proxy.requests.get") as m_get:
            m_session = m.return_value.__enter__.return_value
            m_get.return_value.ok = True
            m_get.return_value.text = "PPD content"

            # no master backend -> same url returned
            m_session.query.return_value.filter.return_value.first.return_value = None
            assert self.proxy.getPPDURL("http://localhost:8050/ppd/modified/fake.ppd") == "http://localhost:8050/ppd/modified/fake.ppd"

            m_session.query.return_value.filter.return_value.first.return_value = mock.MagicMock()
            m_session.query.return_value.filter.return_value.first.return_value.url = "http://master-server:8050"

            # no valid response
            m_get.return_value.ok = False
            m_get.return_value.status_code.return_value = 404
            assert self.proxy.getPPDURL("http://localhost:8050/ppd/modified/fake.ppd") == "http://localhost:8050/ppd/modified/fake.ppd"

            # fake master backend
            m_get.return_value.ok = True
            m_get.return_value.status_code.return_value = 200

            res = self.proxy.getPPDURL("http://localhost:8050/ppd/modified/fake.ppd")
            assert res == "http://localhost:8050/ppd-proxy/master-server/ppd/modified/fake.ppd"
            # check if the file exists
            local_file = os.path.join(self.proxy.ppd_dir, "master-server", "ppd", "modified", "fake.ppd")
            assert os.path.exists(local_file) is True
            with open(local_file) as f:
                assert f.read() == "PPD content"

            # remote URL
            res = self.proxy.getPPDURL("http://any-server/ppd/file.ppd")
            assert res == "http://localhost:8050/ppd-proxy/any-server/ppd/file.ppd"
            # check if the file exists
            local_file = os.path.join(self.proxy.ppd_dir, "any-server", "ppd", "file.ppd")
            assert os.path.exists(local_file) is True
            with open(local_file) as f:
                assert f.read() == "PPD content"
