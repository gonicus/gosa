qx.Class.define("gosa.test.engine.WidgetRegistryTest",
{
  extend : qx.dev.unit.TestCase,

  members :
  {
    testAddAndGetWidget : function() {
      var registry = new gosa.engine.WidgetRegistry();

      // no entry
      this.assertUndefined(registry.getMap().foo);

      // one entry
      var widget = new qx.ui.basic.Label();
      registry.addWidget("foo", widget);
      this.assertEquals([widget, registry.getMap().foo);

      // removing all widgets
      registry.removeAndDisposeAllWidgets();
      this.assertObjectEquals({}, registry.getMap());
    }
  }
});
