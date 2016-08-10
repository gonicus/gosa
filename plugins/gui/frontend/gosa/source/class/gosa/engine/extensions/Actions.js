/**
 * Reads and evaluates actions (e.g. "change password").
 */
qx.Class.define("gosa.engine.extensions.Actions", {
  extend: qx.core.Object,

  implement : [gosa.engine.extensions.IExtension],

  members : {

    process : function(data, target) {
      console.log("TODO: process actions (data: %O, target: %O)", data, target);
    }
  },

  defer : function() {
    gosa.engine.ExtensionManager.getInstance().registerExtension("actions", gosa.engine.extensions.Actions);
  }
});
