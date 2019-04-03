# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
import unittest.mock
import pytest
from gosa.common import Environment
from gosa.common.utils import *
from datetime import timedelta
from lxml import objectify
from io import StringIO
from urllib.error import *

class Type1:
    def __init__(self):
        self.prop1 = "TEST"
class Type2:
    def __init__(self):
        self.prop1 = "TEST"
        self.prop2 = set()

class ModStringIO(StringIO):
    def __init__(self, *args, **kwargs):
        super(ModStringIO, self).__init__(*args, **kwargs)
        self.closeCalls = 0
        self.name = "/random/directory/file"
    def close(self, really=False):
        if really:
            super(ModStringIO, self).close()
        else:
            self.closeCalls += 1

class CommonUtilsTestCase(unittest.TestCase):
    def test_stripNs(self):
        full_xml = """{testNs}Key=Value"""
        expected = """Key=Value"""
        
        assert stripNs(full_xml) == expected
    
    def test_makeAuthURL(self):
        url = "https://hostname.org:1234/example"
        username = "peter"
        password = "secret"
        
        expected = "https://peter:secret@hostname.org:1234/example"
        
        assert makeAuthURL(url, username, password) == expected
    
    def test_parseURL(self):
        url = ""
        assert parseURL(url) == None
        
        url = """https://peter:secret@hostname.org/example/test"""
        expected = {"source": url,
            "scheme": "https",
            "user": "peter",
            "password": "secret",
            "host": "hostname.org",
            "port": 443,
            "path": "example/test",
            "transport": "tcp+ssl",
            "url": "https://peter:secret@hostname.org:443/example/test"
            }
        assert parseURL(url) == expected
        
        url = """http://peter:secret@hostname.org"""
        expected = {"source": url,
            "scheme": "http",
            "user": "peter",
            "password": "secret",
            "host": "hostname.org",
            "port": 80,
            "path": "rpc",
            "transport": "tcp",
            "url": "http://peter:secret@hostname.org:80/rpc"
            }
        assert parseURL(url) == expected
        
        url = """https://hostname.org:1234"""
        expected = {"source": url,
            "scheme": "https",
            "user": None,
            "password": None,
            "host": "hostname.org",
            "port": 1234,
            "path": "rpc",
            "transport": "tcp+ssl",
            "url": "https://None:None@hostname.org:1234/rpc"
            }
        assert parseURL(url) == expected
    
    def test_N_(self):
        assert N_("Not yet translated") == "Not yet translated"
    
    def test_is_uuid(self):
        import uuid
        assert is_uuid("".join([str(x) for x in range(36)])) == False
        assert is_uuid("anything") == False
        for i in range(10):
            assert is_uuid(str(uuid.uuid1())) == True
            assert is_uuid(str(uuid.uuid4())) == True
    
    def test_get_timezone_delta_mocked(self):
        orig_datetime = datetime.datetime(2016, 7, 1, 10, 16, 36, 163915)
        delta = timedelta(hours=2)
        
        with unittest.mock.patch.object(datetime, "datetime", unittest.mock.Mock(wraps=datetime.datetime)) as datetimeMock:
            datetimeMock.now.return_value = orig_datetime
            datetimeMock.utcfromtimestamp.side_effect = [orig_datetime-delta, orig_datetime, orig_datetime+delta]
            datetimeMock.fromtimestamp.return_value = orig_datetime
            
            assert get_timezone_delta() == "+02:00"
            assert get_timezone_delta() == "+00:00"
            assert get_timezone_delta() == "-02:00"
    
    @unittest.mock.patch("os.pathsep", ":")
    @unittest.mock.patch.object(os, "access")
    @unittest.mock.patch.object(os.path, "isfile")
    def test_locate(self, isfileMock, accessMock):
        def isfile(path):
            if path in ("/usr/bin/existanttool", "/bin/existanttool"):
                return True
            return False
        def access(path, mode):
            if mode == os.X_OK:
                if path in ("/usr/bin/existanttool", "/bin/existanttool"):
                    return True
            else:
                raise NotImplementedError
            return False
        
        isfileMock.side_effect = isfile
        accessMock.side_effect = access
        
        with unittest.mock.patch.dict("os.environ", {"PATH": "/usr/bin:/bin"}):
            exe = "/usr/bin/existanttool"
            assert locate(exe) == "/usr/bin/existanttool"
            exe = "/bin/existanttool"
            assert locate(exe) == "/bin/existanttool"
            exe = "existanttool"
            assert locate(exe) == "/usr/bin/existanttool"
            
            exe = "/usr/bin/notexistanttool"
            assert locate(exe) == None
            exe = "notexistanttool"
            assert locate(exe) == None
        
    def test_f_print(self):
        # f_print only works if data is a string or an iterable longer than 1 (indexes 0 and 1).
        
        # Following implementation would be more idiomatic and robust:
        # def f_print(basestr, *values):
        #     return basestr % values
        data = "Testing"
        assert f_print(data) == "Testing"
        
        data = ("A %s string with %s.", "short", "variables")
        assert f_print(data) == "A short string with variables."
        
        data = ("A %s string with %s.", "short", "too", "many", "variables")
        self.assertRaises(TypeError, f_print, data)
        
        data = ("A %s string with %s %s.", "long", "variables")
        self.assertRaises(TypeError, f_print, data)
    
    def test_repr2json(self):
        obj = {"err": "data", "list": [12.00, 12, "12"]}
        assert repr2json(obj.__repr__()) in ("""{"list":[12.0,12,"12"],"err":"data"}""", """{"err":"data","list":[12.0,12,"12"]}""")
        
        # Handle tuples specially?
    
    @unittest.mock.patch("os.sep", "/")
    def downloadFileTest(self, url, expectedFilePath, errorToRaise, **kwargs):
        with unittest.mock.patch("gosa.common.utils.urllib2") as urllib2Mock:
            targetFile = ModStringIO("")
            downloadData = ModStringIO("downloaded content")
            try:
                request = object()
                def urlopenFunc(r):
                    if errorToRaise == HTTPError:
                        raise errorToRaise(None, None, None, None, None)
                    elif errorToRaise == URLError:
                        raise errorToRaise(None, None)
                    elif errorToRaise:
                        raise errorToRaise()
                    assert r == request
                    return downloadData
                urllib2Mock.Request.return_value = request
                urllib2Mock.urlopen.side_effect = urlopenFunc
                with unittest.mock.patch("gosa.common.utils.open", create=True) as openMock:
                    def openFunc(path, mode):
                        assert path == expectedFilePath
                        assert mode == "w"
                        return targetFile
                    openMock.side_effect = openFunc
                    downloadFile(url, **kwargs)
                    assert targetFile.getvalue() == downloadData.getvalue()
            finally:
                downloadData.close(True)
                targetFile.close(True)
            # Input stream is never explicitly closed...
            #assert downloadData.closeCalls == 1
            assert targetFile.closeCalls == 1
    
    @unittest.mock.patch("tempfile.mkdtemp")
    @unittest.mock.patch("tempfile.NamedTemporaryFile")
    def test_downloadFile(self, NamedTemporaryFileMock, mkdtempMock):
        with pytest.raises(ValueError):
            downloadFile(None)
        with pytest.raises(ValueError):
            downloadFile(2)
        with pytest.raises(ValueError):
            downloadFile("abc://test/test")
        
        self.downloadFileTest("http://localhost/test", "/test/downloads/test", None, download_dir="/test/downloads", use_filename=True)
        
        # NamedTemporaryFile file object is used to obtain the name only.
        # The same file is opened after that again.
        ntf = ModStringIO("")
        NamedTemporaryFileMock.return_value = ntf
        try:
            self.downloadFileTest("http://localhost/test", "/random/directory/file", None)
        finally:
            if not ntf.closeCalls:
                ntf.close(True)
        
        ntf = ModStringIO("")
        ntf.name = "/test/downloads/test"
        NamedTemporaryFileMock.return_value = ntf
        try:
            self.downloadFileTest("http://localhost/test", "/test/downloads/test", None, download_dir="/test/downloads")
        finally:
            if not ntf.closeCalls:
                ntf.close(True)
        
        mkdtempMock.return_value = "/random/tmpdir"
        self.downloadFileTest("http://localhost/test", "/random/tmpdir/test", None, use_filename=True)
        
        with pytest.raises(HTTPError):
            self.downloadFileTest("http://localhost/test", "/random/tmpdir/test", HTTPError, use_filename=True)
        with pytest.raises(URLError):
            self.downloadFileTest("http://localhost/test", "/random/tmpdir/test", URLError, use_filename=True)
        with pytest.raises(BaseException):
            self.downloadFileTest("http://localhost/test", "/random/tmpdir/test", BaseException, use_filename=True)
    
    def test_xml2dict(self):
        root = objectify.XML("""
        <root>
            <test>
                <attr>Data1</attr>
            </test>
            <test>
                <attr>Data1</attr>
                <attrtwo>2</attrtwo>
            </test>
            <AttrList>
                <attr>TEST</attr>
            </AttrList>
        </root>
        """)
        assert xml2dict(root) == {"test": [{"attr": "Data1"}, {"attrtwo": "2", "attr": "Data1"}], "AttrList": {"attr": "TEST"}}
        assert xml2dict(Type1()) == {"prop1": "TEST"}
        with pytest.raises(Exception):
            xml2dict(Type2())

    def test_find_api_service(self):

        class Result:
            def __init__(self, prio, w, t, p):
                self.priority = prio
                self.weight = w
                self.target = t
                self.port = p

        with unittest.mock.patch("gosa.common.utils.dns.resolver.query", return_value=[Result(100, 50, "localhost_", 8080)]):
            assert find_api_service() == ["https://localhost:8080/rpc"]
            with unittest.mock.patch.object(Environment.getInstance().config, "get", side_effect=['example.net', '10:0:gosa.intranet.gonicus.de:8050']):
                assert find_api_service() == ["https://gosa.intranet.gonicus.de:8050/rpc"]

    def test_find_bus_service(self):

        class Result:
            def __init__(self, prio, w, t, p):
                self.priority = prio
                self.weight = w
                self.target = t
                self.port = p

        result = [
            Result(100, 50, "localhost_", 8080),
            Result(100, 10, "localhost1_", 8080)
        ]
        with unittest.mock.patch("gosa.common.utils.dns.resolver.query", return_value=result) as m_query:
            assert find_bus_service()[0] == ("localhost", 8080)

            m_query.return_value = [Result(100, 10, "localhost1_", 8080), Result(100, 50, "localhost_", 8080)]
            assert find_bus_service()[0] == ("localhost", 8080)

            m_query.side_effect = dns.resolver.NXDOMAIN
            with unittest.mock.patch("gosa.common.utils.socket.getfqdn", return_value="invalid-domain"):
                assert find_bus_service() == []

            with unittest.mock.patch.object(Environment.getInstance().config, "get", side_effect=['example.net', '10:50:gosa-bus2.intranet.gonicus.de:8883, 10:60:gosa-bus1.intranet.gonicus.de:8883']):
                res = find_bus_service()
                assert res[0] == ("gosa-bus1.intranet.gonicus.de", 8883)
                assert res[1] == ("gosa-bus2.intranet.gonicus.de", 8883)


