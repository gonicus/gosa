#!/usr/bin/python3

import platform
import unittest, unittest.mock, pytest
from gosa.common.config import *

orig_exc = configparser.NoSectionError
orig_join = os.path.join

class ConfigTestCase(unittest.TestCase):
    @unittest.mock.patch("gosa.common.config.ArgumentParser")
    @unittest.mock.patch("gosa.common.config.configparser")
    @unittest.mock.patch("gosa.common.config.logging.config")
    @unittest.mock.patch("gosa.common.config.logging")
    @unittest.mock.patch("gosa.common.config.os")
    def test_Config(self, osMock, loggingMock, loggingConfigMock, configparserMock, argParserMock):
        configparserMock.NoSectionError = orig_exc
        osMock.path.join = orig_join
        def listdir(path):
            if path in {"/fake/etc/gosa/config.d", "/fake2/etc/gosa/config.d", "/fake3/etc/gosa/config.d"}:
                return ["moreConf.conf", "notconf"]
            else:
                raise OSError
        def isfile(path):
            return path in {"/fake/etc/gosa/config.d/moreConf.conf", "/fake2/etc/gosa/config.d/moreConf.conf", "/fake3/etc/gosa/config.d/moreConf.conf"}
        osMock.path.isfile.side_effect = isfile
        osMock.listdir.side_effect = listdir
        rawConfigParserMock = unittest.mock.MagicMock()
        rawConfigParserMock.read.return_value = ["/fake/etc/gosa/config", "/fake/etc/gosa/config.d/moreConf.conf"]
        rawConfigParserMock.sections.return_value = ["section1", "section2"]
        def items(section):
            if section == "section1":
                return {"key": "value", "property": "value"}
            elif section == "section2":
                return {"alittlebit": "config"}
        rawConfigParserMock.items.side_effect = items
        configparserMock.RawConfigParser.return_value = rawConfigParserMock
        
        c = Config(config="/fake/etc/gosa", noargs=True)
        
        assert loggingConfigMock.fileConfig.call_count
        
        assert c.getBaseDir() == "/fake/etc/gosa"
        
        assert set(c.getSections()) == set(["core", "section1", "section2"])
        assert c.getOptions("section1") == {"key": "value", "property": "value"}
        assert c.getOptions("section2") == {"alittlebit": "config"}
        assert c.get("section1.key") == "value"
        assert c.get("section1.notexistant", default="default") == "default"
        rawConfigParserMock.read.assert_called_with(["/fake/etc/gosa/config", "/fake/etc/gosa/config.d/moreConf.conf"])
        
        # Test handling of configparser.NoSectionError
        loggingConfigMock.fileConfig.side_effect = configparser.NoSectionError("Failure")
        c = Config(config="/fake/etc/gosa", noargs=True)
        loggingMock.basicConfig.assert_called_with(level=loggingMock.ERROR, format="%(asctime)s (%(levelname)s): %(message)s")
        loggingConfigMock.fileConfig.side_effect = None
        
        # Test ArgumentParser usage
        with unittest.mock.patch.object(sys, "argv", ["--config", "/fake2/etc/gosa"]):
            rawConfigParserMock.read.return_value = ["/fake2/etc/gosa/config", "/fake2/etc/gosa/config.d/moreConf.conf"]
            optionsMock = unittest.mock.MagicMock()
            optionsMock.__dict__ = {"config": "/fake2/etc/gosa"}
            parserMock = unittest.mock.MagicMock()
            parserMock.parse_known_args.return_value = (optionsMock, ["--config", "/fake2/etc/gosa"])
            argParserMock.return_value = parserMock
            c = Config(noargs=False)
            argParserMock.assert_called_with(usage="%(prog)s - the gosa daemon")
            parserMock.add_argument.call_args_list == [unittest.mock.call("--version", action='version', version=VERSION),
                    unittest.mock.call("-c", "--config", dest="config", 
                        default="/etc/gosa",
                        help="read configuration from DIRECTORY [%(default)s]",
                        metavar="DIRECTORY")]
            parserMock.parse_known_args.assert_called_with()
            
            assert c.get("core.config") == "/fake2/etc/gosa"
            rawConfigParserMock.read.assert_called_with(["/fake2/etc/gosa/config", "/fake2/etc/gosa/config.d/moreConf.conf"])
        
        # Test detection of environment variable "GOSA_CONFIG_DIR"
        osMock.environ = {"GOSA_CONFIG_DIR": "/fake3/etc/gosa"}
        c = Config(noargs=True)
        assert c.getBaseDir() == "/fake3/etc/gosa"
        rawConfigParserMock.read.assert_called_with(["/fake3/etc/gosa/config", "/fake3/etc/gosa/config.d/moreConf.conf"])
        # Test use of default value "/etc/gosa"
        osMock.environ = {}
        c = Config(noargs=True)
        assert c.getBaseDir() == "/etc/gosa"
        
        # Test if non-Windows data is loaded
        if platform.system() != "Windows":
            with unittest.mock.patch("gosa.common.config.pwd") as pwdMock,\
                    unittest.mock.patch("gosa.common.config.grp") as grpMock,\
                    unittest.mock.patch("gosa.common.config.getpass") as getpassMock:
                c = Config(noargs=True)
                assert c.get("core.user") == getpassMock.getuser()
                assert c.get("core.group") == grpMock.getgrgid(pwdMock.getpwnam(c.get("core.user")).pw_gid).gr_name
        
        # Trigger raise of OSError
        osMock.listdir.side_effect = OSError
        Config(config="/fake/etc/gosa", noargs=True)
        rawConfigParserMock.read.assert_called_with(["/fake/etc/gosa/config"])
        osMock.listdir.side_effect = None
        
        # Trigger raise of ConfigNoFile
        rawConfigParserMock.read.return_value = []
        with pytest.raises(ConfigNoFile):
            Config(config="/fake/etc/gosa", noargs=True)
        
        
