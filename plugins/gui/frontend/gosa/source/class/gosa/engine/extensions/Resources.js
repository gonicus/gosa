/**
 * Reads and evaluates resources, e.g. image paths, font icons.
 */
qx.Class.define("gosa.engine.extensions.Resources", {
  extend: qx.core.Object,

  implement : [gosa.engine.extensions.IExtension],

  members : {

    process : function(data, target, context) {
      var resourceManager = context.getResourceManager();
      for (var key in data) {
        if (data.hasOwnProperty(key)) {
          resourceManager.addResource(key, data[key]);
        }
      }
    }
  },

  defer : function() {
    gosa.engine.ExtensionManager.getInstance().registerExtension("resources", gosa.engine.extensions.Resources);
  }
});
