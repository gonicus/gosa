/**
 * Reads the gui properties from the template and applies them to the widget.
 */
qx.Class.define("gosa.engine.extensions.GuiProperties", {
  extend: qx.core.Object,

  implement : [gosa.engine.extensions.IExtension],

  members : {

    process : function(data, target) {
      target.setGuiProperties(data);
    }
  },

  defer : function() {
    gosa.engine.ExtensionManager.getInstance().registerExtension("guiProperties", gosa.engine.extensions.GuiProperties);
  }
});
