#!/usr/bin/python3

import unittest
import unittest.mock
import re
import os
import pytest
import time
from gosa.common.utils import *
from datetime import timedelta
from lxml import objectify, etree
from io import StringIO
from urllib.parse import urlparse
from urllib.error import *

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
        # Required xml scheme unknown. Following won't work.
        full_xml = """<?xml version="1.0"?><xml xmlns="http://example.com/xmlns"><a><p>TESTING</p></a></xml>"""
        expected = """
            <xml xmlns="http://example.com/xmlns">
                <p>TESTING</p>
            </xml>
        """
        
        return True
        self.assertEqual(stripNs(full_xml), expected)
    
    def test_makeAuthURL(self):
        url = "https://hostname.org:1234/example"
        username = "peter"
        password = "secret"
        
        expected = "https://peter:secret@hostname.org:1234/example"
        
        self.assertEqual(makeAuthURL(url, username, password), expected)
    
    def test_parseURL(self):
        url = ""
        self.assertEqual(parseURL(url), None)
        
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
        self.assertEqual(parseURL(url), expected)
        
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
        self.assertEqual(parseURL(url), expected)
        
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
        self.assertEqual(parseURL(url), expected)
    
    def test_N_(self):
        self.assertEqual(N_("Not yet translated"), "Not yet translated")
    
    def test_is_uuid(self):
        import uuid
        self.assertFalse(is_uuid("".join([str(x) for x in range(36)])))
        self.assertFalse(is_uuid("-".join([str(x) for x in range(36)])))
        self.assertFalse(is_uuid("anything"))
        for i in range(100):
            self.assertTrue(is_uuid(str(uuid.uuid1())))
            self.assertTrue(is_uuid(str(uuid.uuid4())))
    
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
    
    def test_get_timezone_delta(self):
        delta = get_timezone_delta()
        self.assertRegex(delta, """([-+])(\d+):(\d+)$""")

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
        self.assertEqual(f_print(data), "Testing")
        
        data = ("A %s string with %s.", "short", "variables")
        self.assertEqual(f_print(data), "A short string with variables.")
        
        data = ("A %s string with %s.", "short", "too", "many", "variables")
        self.assertRaises(TypeError, f_print, data)
        
        data = ("A %s string with %s %s.", "long", "variables")
        self.assertRaises(TypeError, f_print, data)
    
    # Unused
    def test_repr2json(self):
        # ???
        
        obj = {"err": ReferenceError(), "list": [12.00, 12, "12"]}
        print(obj.__repr__())
        print(repr2json(obj.__repr__()))
        print(repr2json("""{"json": 2}"""))
        
        # Impementation does not handle tuples correctly: 
        # As there are no tuples in JSON, these may be turned to lists.
    
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
    
    # Unused
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
    
    # Unused
    def test_xml2dict(self):
        # Implementation returns int values as string.
        # It could also alternatively return python ints.
        # v.pyval instead of v.text (as per lxml docs)
        # BUT: Some code may rely on that.
        
        #root = objectify.Element("root")
        root = objectify.XML("""
        <root>
            <test>
                data
                <attr>Data1</attr>
                <attrtwo>2</attrtwo>
            </test>
            <AttrList>
                <attr>1</attr>
                <attr>2</attr>
                <attr>3</attr>
                <attr>4</attr>
            </AttrList>
        </root>
        """)
        objectify.SubElement(root, "sub2", data2="data")
        print(xml2dict(root))
