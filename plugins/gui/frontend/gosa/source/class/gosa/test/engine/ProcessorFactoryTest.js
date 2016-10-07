qx.Class.define("gosa.test.engine.ProcessorFactoryTest",
{
  extend : qx.dev.unit.TestCase,

  members :
  {
    testProcessorFactory : function() {
      var factory = gosa.engine.ProcessorFactory;

      var json = JSON.parse('{"type" : "widget"}');
      this.assertInstance(factory.getProcessor(json), gosa.engine.processors.WidgetProcessor);

      json = JSON.parse('{"type" : "form"}');
      this.assertInstance(factory.getProcessor(json), gosa.engine.processors.FormProcessor);

      json = JSON.parse('{"type" : "foo"}');
      this.assertNull(factory.getProcessor(json));
    }
  }
});
