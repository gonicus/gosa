qx.Class.define("gosa.test.engine.ExtensionManagerTest",
{
  extend : qx.dev.unit.TestCase,

  members :
  {
    testRegisterAndHandleExtension : function() {
      var manager = gosa.engine.ExtensionManager.getInstance();
      manager.registerExtension("foo", gosa.test.engine.SampleExtension);

      this.assertException(function() {manager.registerExtension("foo", gosa.test.engine.SampleExtension);});

      manager.handleExtension("foo", "bar", manager);
    }
  }
});
