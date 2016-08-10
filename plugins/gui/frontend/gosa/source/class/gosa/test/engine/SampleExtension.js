qx.Class.define("gosa.test.engine.SampleExtension", {

  extend : qx.core.Object,
  implement : [gosa.engine.extensions.IExtension],
  include : [qx.core.MAssert],

  members : {

    process : function(data, target) {
      this.assertEquals("bar", data);
      this.assertEquals(gosa.engine.ExtensionManager.getInstance(), target);
    }
  }
});
