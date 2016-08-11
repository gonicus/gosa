/**
 * Configuration for a tab page where a template is shown.
 */
qx.Class.define("gosa.engine.extensions.TabConfig", {
  extend: qx.core.Object,

  implement : [gosa.engine.extensions.IExtension],

  members : {

    process : function(data, target) {
      qx.core.Assert.assertObject(data);

      var tabPage = this._findTabPage(target);
      if (!tabPage) {
        this.error("No tab page found for target '" + target + "'.");
        return;
      }

      // set values
      if (data.hasOwnProperty("title")) {
        tabPage.setLabel(data.title);
      }
    },

    _findTabPage : function(target) {
      if (target instanceof qx.ui.tabview.Page) {
        return target;
      }

      var widget = target;
      while (widget.getLayoutParent()) {
        widget = widget.getLayoutParent();
        if (widget instanceof qx.ui.tabview.Page) {
          return widget;
        }
      }
      return null;
    }
  },

  defer : function() {
    gosa.engine.ExtensionManager.getInstance().registerExtension("tabConfig", gosa.engine.extensions.TabConfig);
  }
});
