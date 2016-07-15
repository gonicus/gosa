#!/usr/bin/python3

import unittest, pytest
import unittest.mock
from gosa.common.env import *

class EnvTestCase(unittest.TestCase):
    @unittest.mock.patch("gosa.common.env.sessionmaker")
    @unittest.mock.patch("gosa.common.env.scoped_session")
    @unittest.mock.patch("gosa.common.env.create_engine")
    @unittest.mock.patch("gosa.common.env.Config")
    @unittest.mock.patch("gosa.common.env.logging")
    def test_Environment(self, loggingMock, configMock, createEngineMock, scopedSessionMock, sessionmakerMock):
        # __init__:
        loggerMock = unittest.mock.MagicMock()
        loggerMock.getEffectiveLevel.return_value = loggingMock.DEBUG
        loggingMock.getLogger.return_value = loggerMock
        
        def getOptions(section):
            if section == "section":
                return {"option": "value", "key": "val"}
            else:
                return {"opt": "v"}
        confMock = unittest.mock.MagicMock()
        confMock.getSections.return_value = ["section", "other"]
        confMock.getOptions.side_effect = getOptions
        configMock.return_value = confMock
        
        e = Environment.getInstance()
        
        assert loggerMock.debug.call_args_list[0] == unittest.mock.call("configuration dump:")
        assert loggerMock.debug.call_args_list[1] == unittest.mock.call("[section]")
        # As implementation iterates a dict the order is not defined
        assert unittest.mock.call("option = value") in loggerMock.debug.call_args_list[2:4]
        assert unittest.mock.call("key = val") in loggerMock.debug.call_args_list[2:4]
        assert loggerMock.debug.call_args_list[4] == unittest.mock.call("[other]")
        assert loggerMock.debug.call_args_list[5] == unittest.mock.call("opt = v")
        assert loggerMock.debug.call_args_list[6] == unittest.mock.call("end of configuration dump")
        
        # requestRestart:
        e.requestRestart()
        loggerMock.warning.assert_called_with("a component requested an environment reset")
        assert e.reset_requested == True
        
        # getDatabaseEngine:
        dsnames = {"db1.dbs": "db1datasourcename", "db2.dbs": "db2datasourcename"}
        engines = {"db1datasourcename": unittest.mock.MagicMock(), "db2datasourcename": unittest.mock.MagicMock()}
        sessions = {engines["db1datasourcename"]: unittest.mock.MagicMock(), engines["db2datasourcename"]: unittest.mock.MagicMock()}
        def createEngine(dsn):
            return engines[dsn]
        createEngineMock.side_effect = createEngine
        def get(index, default=None):
            if index in dsnames:
                return dsnames[index]
            elif index == "notexistant.dbs":
                return None
            else:
                return unittest.mock.MagicMock()
        confMock.get.side_effect = get
        
        assert e.getDatabaseEngine("db1", key="dbs") == engines["db1datasourcename"]
        with pytest.raises(Exception):
            e.getDatabaseEngine("notexistant", key="dbs")
        
        e.getDatabaseSession("db1", key="dbs")
        
        scopedSessionMock.assert_called_with(sessionmakerMock(autoflush=True))
        
        assert e == Environment.getInstance()
        
        del e
        Environment.reset()
        
        Environment.getInstance()
        
        # Note: References of the Environment object may be hold by others.
        # An reset followed by getInstance would lead to multiple instances.
