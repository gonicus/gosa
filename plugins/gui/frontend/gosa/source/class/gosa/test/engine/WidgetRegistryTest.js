qx.Class.define("gosa.test.engine.WidgetRegistryTest",
{
  extend : qx.dev.unit.TestCase,

  members :
  {
    testAddAndGetWidget : function() {
      var registry = gosa.engine.WidgetRegistry.getInstance();

      // no entry
      this.assertArrayEquals([], registry.getWidgetsByName("foo"));

      // one entry
      var widget = new qx.ui.basic.Label();
      registry.addWidget("foo", widget);
      this.assertArrayEquals([widget], registry.getWidgetsByName("foo"));

      // two entries
      var widget2 = new qx.ui.basic.Label();
      registry.addWidget("foo", widget2);
      this.assertArrayEquals([widget, widget2], registry.getWidgetsByName("foo"));

      var widget3 = new qx.ui.basic.Label();
      registry.removeWidget(widget3);
      registry.removeWidgetsByName("bar");
      this.assertArrayEquals([widget, widget2], registry.getWidgetsByName("foo"));

      // removing one widget
      registry.removeWidget(widget);
      this.assertArrayEquals([widget2], registry.getWidgetsByName("foo"));

      // removing all widgets
      registry.addWidget("foo", widget);
      registry.addWidget("foo", widget3);
      registry.removeWidgetsByName("foo");
      this.assertArrayEquals([], registry.getWidgetsByName("foo"));
    }
  }
});
