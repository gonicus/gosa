/**
 * Reads and evaluates resources, e.g. image paths, font icons.
 */
qx.Class.define("gosa.engine.extensions.Resources", {
  extend: qx.core.Object,

  implement : [gosa.engine.extensions.IExtension],

  members : {

    process : function(data, target) {
      console.log("TODO: process resources (data: %O, target: %O)", data, target);
    }
  },

  defer : function() {
    gosa.engine.ExtensionManager.getInstance().registerExtension("resources", gosa.engine.extensions.Resources);
  }
});
