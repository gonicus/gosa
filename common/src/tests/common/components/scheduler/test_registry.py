#!/usr/bin/python3

import unittest, pytest
from gosa.common.components.registry import *

class RegistryTestCase(unittest.TestCase):
    def test_PluginRegistry(self):
        # Use of only one test method to guarantee right execution order
        
        with unittest.mock.patch.object(PluginRegistry, "getEventSchema") as getEventSchemaMock,\
                unittest.mock.patch("gosa.common.components.registry.etree") as etreeMock,\
                unittest.mock.patch("gosa.common.components.registry.objectify") as objectifyMock:
            assert PluginRegistry._event_parser is None
            ep = PluginRegistry.getEventParser()
            
            etreeMock.XML.assert_called_once_with(getEventSchemaMock())
            schema_root = etreeMock.XML(getEventSchemaMock())
            etreeMock.XMLSchema.assert_called_once_with(schema_root)
            schema = etreeMock.XMLSchema(schema_root)
            objectifyMock.makeparser.assert_called_once_with(schema=schema)
            parser = objectifyMock.makeparser(schema=schema)
            
            assert PluginRegistry._event_parser is ep is PluginRegistry.getEventParser() is parser
        
        with unittest.mock.patch("gosa.common.components.registry.Environment") as EnvironmentMock,\
                unittest.mock.patch("gosa.common.components.registry.logging") as loggingMock,\
                unittest.mock.patch("gosa.common.components.registry.resource_filename") as resource_filenameMock,\
                unittest.mock.patch("gosa.common.components.registry.resource_isdir") as resource_isdirMock,\
                unittest.mock.patch("gosa.common.components.registry.resource_listdir") as resource_listdirMock,\
                unittest.mock.patch("gosa.common.components.registry.iter_entry_points") as iter_entry_pointsMock,\
                unittest.mock.patch("gosa.common.components.registry.IInterfaceHandler") as IInterfaceHandlerMock,\
                unittest.mock.patch("gosa.common.components.registry.isclass") as isclassMock,\
                unittest.mock.patch("gosa.common.components.registry.etree") as etreeMock:
        
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
