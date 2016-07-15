#!/usr/bin/python3

import unittest, pytest
from gosa.common.components.registry import *

class RegistryTestCase(unittest.TestCase):
    @unittest.mock.patch("gosa.common.components.registry.Environment")
    @unittest.mock.patch("gosa.common.components.registry.logging")
    @unittest.mock.patch("gosa.common.components.registry.resource_filename")
    @unittest.mock.patch("gosa.common.components.registry.resource_listdir")
    @unittest.mock.patch("gosa.common.components.registry.resource_isdir")
    @unittest.mock.patch("gosa.common.components.registry.iter_entry_points")
    @unittest.mock.patch("gosa.common.components.registry.IInterfaceHandler")
    @unittest.mock.patch("gosa.common.components.registry.isclass")
    @unittest.mock.patch("gosa.common.components.registry.etree")
    def test_PluginRegistry(self, etreeMock, isclassMock, IInterfaceHandlerMock, iter_entry_pointsMock,\
            resource_isdirMock, resource_listdirMock, resource_filenameMock, loggingMock, EnvironmentMock):
        # Use of only one test method to guarantee right execution order
        
        loggerMock = unittest.mock.MagicMock()
        loggingMock.getLogger.return_value = loggerMock
        
        # __init__:
        resource_filenameMock.return_value = "/test/filename"
        def addEntryMock(l, implements, modulename, isdir, is_class):
            module_obj = unittest.mock.MagicMock()
            module_obj.is_class.return_value = is_class
            module = unittest.mock.MagicMock()
            module.__name__ = modulename
            module.implementsInterface.return_value = implements
            module.__module__ = unittest.mock.MagicMock()
            module.__module__.isdir.return_value = isdir
            module.is_class.return_value = True
            module.return_value = module_obj
            entry = unittest.mock.MagicMock()
            entry.load.return_value = module
            l.append(entry)
        entries = []
        addEntryMock(entries, True, "Module1", False, True)
        addEntryMock(entries, False, "Module2", True, False)
        
        def implementedBy(module):
            return module.implementsInterface() == True
        IInterfaceHandlerMock.implementedBy.side_effect = implementedBy
        
        iter_entry_pointsMock.return_value = entries
        
        def resource_isdir(module, filepath):
            return module.isdir() == True
        resource_isdirMock.side_effect = resource_isdir
        
        def resource_listdir(module_str, filepath):
            if module_str == "gosa.common":
                return ["globalevent.xsd"]
            elif module_str:
                return ["t.test", "testevent.xsd"]
        resource_listdirMock.side_effect = resource_listdir
        
        pr = PluginRegistry()
        
        assert PluginRegistry.modules == {"Module1": entries[0].load()(), "Module2": entries[1].load()()}
        assert PluginRegistry.handlers == {"Module1": entries[0].load()()}
        assert PluginRegistry.evreg == {"globalevent": "/test/filename/globalevent.xsd", "testevent": "/test/filename/testevent.xsd"}
        
        assert loggerMock.debug.call_args_list == [unittest.mock.call("inizializing plugin registry"),
                unittest.mock.call("adding common event 'globalevent'"),
                unittest.mock.call('registering handler module Module1'),
                unittest.mock.call("adding module event 'testevent'")]
        
        # getInstance:
        with pytest.raises(ValueError):
            PluginRegistry.getInstance("notexistant")
        
        def isclass(module):
            return module.is_class() == True
        isclassMock.side_effect = isclass
        
        assert PluginRegistry.getInstance("Module1") == None
        assert PluginRegistry.getInstance("Module2") == PluginRegistry.modules["Module2"]
        
        # getEventSchema:
        filename = unittest.mock.MagicMock()
        resource_filenameMock.return_value = filename
        xml_doc = unittest.mock.MagicMock()
        xslt_doc = unittest.mock.MagicMock()
        result = object()
        def transform(xml):
            if xml == xml_doc:
                return result
        def parse(source):
            if source == filename:
                return xslt_doc
            else:
                # Implementation iterates over a dict - order of inserted paths
                # is therefore undefined.
                assert source.getvalue() in (("<events><path name=\"globalevent\">/test/filename/globalevent.xsd</path>"
                            "<path name=\"testevent\">/test/filename/testevent.xsd</path></events>"),
                            ("<events><path name=\"testevent\">/test/filename/testevent.xsd</path>"
                            "<path name=\"globalevent\">/test/filename/globalevent.xsd</path></events>"))
                return xml_doc
        etreeMock.parse.side_effect = parse
        def XSLT(source):
            if source == xslt_doc:
                return transform
        etreeMock.XSLT.side_effect = XSLT
        
        assert PluginRegistry.getEventSchema() == str(result)
        
        resource_filenameMock.assert_called_with("gosa.common", "data/events/events.xsl")
        
        # shutdown:
        PluginRegistry.shutdown()
        for c in PluginRegistry.handlers.values():
            c.stop.assert_called_once_with()
