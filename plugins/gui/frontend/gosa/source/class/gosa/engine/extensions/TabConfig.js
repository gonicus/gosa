/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Configuration for a tab page where a template is shown.
 */
qx.Class.define("gosa.engine.extensions.TabConfig", {
  extend: qx.core.Object,

  implement : [gosa.engine.extensions.IExtension],

  members : {

    process : function(data, target, context) {
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
      if (data.hasOwnProperty("icon")) {
        tabPage.setIcon(context.getResourceManager().getResource(data.icon));
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
