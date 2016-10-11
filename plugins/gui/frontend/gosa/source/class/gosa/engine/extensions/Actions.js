/**
 * Reads and evaluates actions (e.g. "change password").
 */
qx.Class.define("gosa.engine.extensions.Actions", {
  extend : qx.core.Object,

  implement : [gosa.engine.extensions.IExtension],

  members : {

    process : function(data, target, context) {
      qx.core.Assert.assertArray(data, "Actions configuration must be an array");
      data.forEach(function(action) {
        this._processAction(action, target, context);
      }, this);
    },

    _processAction : function(data, target, context) {
      qx.core.Assert.assertMap(data, "Action configuration must be a hash map");
      qx.core.Assert.assertKeyInMap("name", data, "Action configuration must have the key 'name'");
      qx.core.Assert.assertKeyInMap("text", data, "Action configuration must have the key 'text'");

      var button = new qx.ui.menu.Button(data.text, context.getResourceManager().getResource(data.icon));
      button.setAppearance("icon-menu-button");

      // TODO: shortcuts, conditions, target
      if (data.hasOwnProperty("dialog")) {
        button.addListener("execute", function() {
          var clazz = qx.Class.getByName("gosa.ui.dialogs.actions." + data.dialog);
          if (!clazz) {
            qx.core.Assert.fail("Cannot find class for dialog '" + data.dialog + "'");
          }
          var dialog = new clazz(context.getActionController());
          dialog.setAutoDispose(true);
          dialog.open();
        });
      }

      context.addActionMenuEntry(data.name, button);
    }
  },

  defer : function() {
    gosa.engine.ExtensionManager.getInstance().registerExtension("actions", gosa.engine.extensions.Actions);
  }
});
