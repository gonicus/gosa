/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

/**
 * This extension provides the same functionality as the <BlockedBy> setting in the object definitions, but in can be used in the templates
 * directly to block widgets without modelPaths.
 */
qx.Class.define("gosa.engine.extensions.BlockedBy", {
  extend: qx.core.Object,

  implement : [gosa.engine.extensions.IExtension],

  members : {

    process : function(data, target, context) {
      var value = data.value;
      var modelPath = data.modelPath;
      var sourceWidget = context.getWidgetRegistry().getMap()[modelPath];
      if (!sourceWidget) {
        this.error("No widget found for modelPath '" + modelPath + "'.");
        return;
      }
      sourceWidget.addListenerOnce("appear", function() {
        target.setVisibility(sourceWidget.getSingleValue() === value ? "excluded" : "visible");
      }, this);

      sourceWidget.addListener("changeValue", function(ev) {
        var v = gosa.ui.widgets.Widget.getSingleValue(ev.getData());
        target.setVisibility(v === value ? "excluded" : "visible");
      }, this);
    }
  },

  defer : function() {
    gosa.engine.ExtensionManager.getInstance().registerExtension("blockedBy", gosa.engine.extensions.BlockedBy);
  }
});
