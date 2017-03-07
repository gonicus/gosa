# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import pytest
from unittest import mock, TestCase
from gosa.shell.main import *
from gosa.common.components.auth import AUTH_FAILED, AUTH_SUCCESS


class SoftspaceTestCase(TestCase):

    def test_softspace(self):

        # use metaclass to create a read-only property
        class ReadableSoftspaceMock:
            __sp = 0

            @property
            def softspace(self):
                return self.__sp

        class WriteableSoftspaceMock:
            softspace = 10

        class NoSoftspaceMock:
            other = 0

        mocked_fn = ReadableSoftspaceMock()
        assert softspace(mocked_fn, 1) == 0
        # read-only softspace not changed
        assert mocked_fn.softspace == 0

        writeable = WriteableSoftspaceMock()
        assert softspace(writeable, 1) == 10
        # writeable => changed
        assert writeable.softspace == 1

        nosoft = NoSoftspaceMock()
        assert softspace(nosoft, 1) == 0


class SseClientTestCase(TestCase):

    def test_on_event(self):
        class MockService():
            proxy = None

        class MockEvent():
            name = 'fake event'

        client = SseClient(MockService())
        with mock.patch("gosa.shell.main.print") as mp:
            client.on_event(MockEvent())
            mp.assert_called_with("Unhandled incoming SSE message:\nfake event")


class MyConsoleTestCase(TestCase):

    def test_getLastCode(self):
        con = MyConsole()

        assert con.getLastCode() is None

        con.lastCode = "test"
        assert con.getLastCode() == "test"

    def test_runcode(self):
        con = MyConsole()
        m_proxy = mock.MagicMock()
        con.proxy = m_proxy

        assert con.getLastCode() is None

        with mock.patch("gosa.shell.main.exec") as m,\
                mock.patch("gosa.shell.main.print") as mp:
            con.runcode("some fake code")
            assert con.getLastCode() == "some fake code"
            with mock.patch("gosa.shell.main.softspace", return_value=1):
                con.runcode("some fake code")
                mp.assert_called_with()

            m.side_effect = HTTPError("", 500, "", "", "")
            with mock.patch.object(con, "showtraceback") as mt:
                con.runcode("some fake code")
                assert mt.called

            m.side_effect = Exception("test error")
            with mock.patch.object(con, "showtraceback") as mt:
                con.runcode("some fake code")
                assert mt.called

            m.side_effect = HTTPError("", 401, "", "", "")
            with pytest.raises(Exception):
                con.runcode("some fake code")
                assert mt.called

            m.side_effect = JSONRPCException({"unknown": "fake error"})
            con.runcode("some fake code")
            mp.assert_called_with("{'unknown': 'fake error'}")

            m.side_effect = JSONRPCException({"error": "fake error"})
            con.runcode("some fake code")
            mp.assert_called_with("fake error")

            with mock.patch("gosa.shell.main.C.get_error_id", return_value='fake_error_id') as m_get_error:
                m_proxy.getError.return_value = {
                    'details': [{
                        'detail': 'Test error details',
                        'index': 0
                    }],
                    'topic': 'Test topic',
                    'text': 'Test error'
                }
                con.runcode("some fake code")
                mp.assert_called_with("Test error - Test error details [0]: Test topic")

                # no topic
                m_proxy.getError.return_value = {
                    'details': [{
                        'detail': 'Test error details',
                        'index': 0
                    }],
                    'topic': '',
                    'text': 'Test error'
                }
                con.runcode("some fake code")
                mp.assert_called_with("Test error - Test error details [0]")

                # no details
                m_proxy.getError.return_value = {
                    'details': '',
                    'topic': '',
                    'text': 'Test error'
                }
                con.runcode("some fake code")
                mp.assert_called_with("Test error")

                with mock.patch("gosa.shell.main.softspace", return_value=1):
                    con.runcode("some fake code")
                    mp.assert_called_with()


class GosaServiceTestCase(TestCase):

    def test_connect(self):
        with mock.patch("gosa.shell.main.JSONServiceProxy") as m:
            m.return_value.login.return_value = {'state': AUTH_SUCCESS}
            service = GosaService()
            (connection, username, password) = service.connect('http://localhost:8000/rpc', 'admin', 'secret')
            assert connection == 'http://localhost:8000/rpc'
            assert username == 'admin'
            assert password == 'secret'
            m.return_value.login.assert_called_with('admin', 'secret')
            m.reset_mock()

            # use find_api_service
            with mock.patch("gosa.shell.main.find_api_service", return_value=['http://localhost:8000/rpc']):
                (connection, username, password) = service.connect('', 'admin', 'secret')
                assert connection == 'http://localhost:8000/rpc'
                assert username == 'admin'
                assert password == 'secret'
                m.return_value.login.assert_called_with('admin', 'secret')
                m.reset_mock()

            # use input
            with mock.patch("gosa.shell.main.find_api_service", return_value=[]),\
                    mock.patch("gosa.shell.main.input", return_value='http://localhost:8000/rpc'):
                (connection, username, password) = service.connect('', 'admin', 'secret')
                assert connection == 'http://localhost:8000/rpc'
                assert username == 'admin'
                assert password == 'secret'
                m.return_value.login.assert_called_with('admin', 'secret')
                m.reset_mock()

            # no service
            with mock.patch("gosa.shell.main.find_api_service", return_value=[]), \
                    mock.patch("gosa.shell.main.input", return_value=''),\
                    pytest.raises(SystemExit):
                service.connect('', 'admin', 'secret')

            # with credentials in url
            (connection, username, password) = service.connect('http://admin:secret@localhost:8000/rpc')
            assert connection == 'http://localhost:8000/rpc'
            assert username == 'admin'
            assert password == 'secret'
            m.return_value.login.assert_called_with('admin', 'secret')
            m.reset_mock()

            # no credentials
            with mock.patch("gosa.shell.main.find_api_service", return_value=[]), \
                    mock.patch("gosa.shell.main.input", return_value='admin') as mi,\
                    mock.patch("gosa.shell.main.getpass.getpass", return_value='secret'):
                (connection, username, password) = service.connect('http://localhost:8000/rpc')
                assert connection == 'http://localhost:8000/rpc'
                assert username == 'admin'
                assert password == 'secret'
                m.return_value.login.assert_called_with('admin', 'secret')
                m.reset_mock()

                # no username input
                mi.return_value = ''
                with mock.patch("gosa.shell.main.getpass.getuser", return_value='admin'):
                    (connection, username, password) = service.connect('http://localhost:8000/rpc')
                    assert connection == 'http://localhost:8000/rpc'
                    assert username == 'admin'
                    assert password == 'secret'
                    m.return_value.login.assert_called_with('admin', 'secret')
                    m.reset_mock()

            # wrong protocol
            with pytest.raises(SystemExit):
                service.connect('ftp://localhost:8000/rpc', 'admin', 'secret')

            # failed login
            m.return_value.login.return_value = {'state': AUTH_FAILED}
            with pytest.raises(SystemExit):
                service.connect('http://localhost:8000/rpc', 'admin', 'secret')

            m.return_value.login.side_effect = Exception("test")
            with pytest.raises(SystemExit):
                service.connect('http://localhost:8000/rpc', 'admin', 'secret')

    def test_reconnectJson(self):
        with mock.patch("gosa.shell.main.JSONServiceProxy") as m:
            m.return_value.login.return_value = {'state': AUTH_SUCCESS}
            service = GosaService()
            service.reconnectJson('http://localhost:8000/rpc', 'admin', 'secret')

            m.return_value.login.return_value = {'state': AUTH_FAILED}
            with pytest.raises(SystemExit):
                service.reconnectJson('http://localhost:8000/rpc', 'admin', 'secret')

            m.return_value.login.side_effect = Exception("test")
            with pytest.raises(SystemExit):
                service.reconnectJson('http://localhost:8000/rpc', 'admin', 'secret')

    def test_help(self):
        with mock.patch("gosa.shell.main.JSONServiceProxy") as m,\
                mock.patch("gosa.shell.main.print") as mp:
            m.return_value.getMethods.return_value = {
                'transliterate': {
                    'name': 'transliterate',
                    'target': 'misc',
                    'type': 1,
                    'doc': 'Transliterate a given string',
                    'sig': ['string'],
                    'path': 'Transliterate.transliterate'
                }
            }
            service = GosaService()
            service.connect('http://localhost:8000/rpc', 'admin', 'secret')
            service.help()

            mp.assert_called_with("  transliterate(string)\n    Transliterate a given string\n")

            with mock.patch("gosa.shell.main.locale.getdefaultlocale", return_value=True):
                service.help()
                m.return_value.getMethods.assert_called_with(None)

    def test_setTwoFactorMethod(self):
        with mock.patch("gosa.shell.main.JSONServiceProxy") as m,\
                mock.patch("gosa.shell.main.pyqrcode") as m_qr,\
                mock.patch("gosa.shell.main.print") as m_print:
            service = GosaService()
            service.proxy = m.return_value
            service.proxy.setTwoFactorMethod.return_value = None
            service.setTwoFactorMethod("fake-dn", "otp")
            assert not m_print.called

            service.proxy.setTwoFactorMethod.return_value = "anything"
            service.setTwoFactorMethod("fake-dn", "otp")
            m_print.assert_called_with("anything")

            service.proxy.setTwoFactorMethod.return_value = "otpauth://fake-string-to-encode"
            service.setTwoFactorMethod("fake-dn", "otp")
            m_qr.create.assert_called_with("otpauth://fake-string-to-encode", error='L')


class MainTestCase(TestCase):

    def test_main(self):
        # print help
        assert main(argv=['-h']) == 0

        with mock.patch("gosa.shell.main.getopt.getopt", side_effect=getopt.GetoptError("test error")) as m_getopt:
            with pytest.raises(SystemExit):
                main()

            m_getopt.side_effect = None
            m_getopt.return_value = ([('-u', 'admin'), ('-p', 'secret'), ('-c', 'fake command;'), ('-d', '')],
                                     ['http://localhost:8000/rpc'])

            with mock.patch("gosa.shell.main.GosaService") as m_service,\
                    pytest.raises(SystemExit):
                m_service.return_value.connect.side_effect = KeyboardInterrupt()
                main()

            with mock.patch("gosa.shell.main.JSONServiceProxy") as m,\
                    mock.patch("gosa.shell.main.SseClient") as m_sse:
                m.return_value.login.return_value = {'state': AUTH_SUCCESS}

                # script mode
                with mock.patch("gosa.shell.main.sys.stdin.isatty", return_value=False), \
                        mock.patch("gosa.shell.main.sys.stdin.read", return_value="fake code"), \
                        mock.patch("gosa.shell.main.code.InteractiveInterpreter") as m_console:
                    assert main() == 0
                    m_console.return_value.runcode.assert_called_with("fake code")
                    args, kwargs = m_sse.return_value.connect.call_args_list[0]
                    assert args[0] == "http://localhost:8000/events"

                    m_console.return_value.runcode.side_effect = Exception("test error")
                    assert main() == 1

                # one shot mode
                with mock.patch("gosa.shell.main.sys.stdin.isatty", return_value=True), \
                        mock.patch("gosa.shell.main.sys.stdin.read", return_value="fake code"), \
                        mock.patch("gosa.shell.main.code.InteractiveInterpreter") as m_console:
                    assert main([0, 1, 2, 3, 4, 5]) == 0
                    m_console.return_value.runcode.assert_called_with("\nimport sys, traceback\ntry:\n    fake command\nexcept:\n    "
                                                                      "traceback.print_exc()\n    sys.exit(1)\n")
                    args, kwargs = m_sse.return_value.connect.call_args_list[0]
                    assert args[0] == "http://localhost:8000/events"

                    m_console.return_value.runcode.side_effect = Exception("test error")
                    assert main([0, 1, 2, 3, 4, 5]) == 1

                # interactive mode
                with mock.patch("gosa.shell.main.sys.stdin.isatty", return_value=True), \
                        mock.patch("gosa.shell.main.MyConsole") as m_console:
                    assert main() == 0
                    param = m_console.return_value.runcode.call_args[0][0]
                    assert param.startswith("\nimport readline\nimport rlcompleter")
                    args, kwargs = m_sse.return_value.connect.call_args_list[0]
                    assert args[0] == "http://localhost:8000/events"

                    m_console.reset_mock()
                    # simulate HTTPError 401
                    m_console.return_value.runcode.side_effect = [HTTPError("", 401, "", "", ""), True]
                    m_console.return_value.getLastCode.return_value = "last code"
                    assert main() == 0
                    m_console.return_value.runcode.assert_called_with("last code")

                    m_console.reset_mock()
                    # simulate HTTPError 500
                    m_console.return_value.runcode.side_effect = HTTPError("", 500, "", "", "")
                    with pytest.raises(SystemExit):
                        main()
