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
 * Options for the layout of a widget that cannot be made via "layoutConfig" in the json template.
 */
qx.Class.define("gosa.engine.extensions.LayoutOptions", {
  extend: qx.core.Object,

  implement : [gosa.engine.extensions.IExtension],

  members : {

    process : function(data, target) {
      qx.core.Assert.assertObject(data);
      qx.core.Assert.assertQxWidget(target);

      this.__processColumnFlex(data, target);
    },

    __processColumnFlex : function(data, target) {
      if (!data.hasOwnProperty("columnFlex")) {
        return;
      }

      var flexConfig = data.columnFlex;
      qx.core.Assert.assertKeyInMap("column", flexConfig);
      qx.core.Assert.assertKeyInMap("flex", flexConfig);

      // one or several columns?
      if (typeof flexConfig.column === "object") {
        for (var i = 0; i < flexConfig.column.length; i++) {
          target.getLayout().setColumnFlex(flexConfig.column[i], flexConfig.flex);
        }
      }
      else {
        target.getLayout().setColumnFlex(flexConfig.column, flexConfig.flex);
      }
    }
  },

  defer : function() {
    gosa.engine.ExtensionManager.getInstance().registerExtension("layoutOptions", gosa.engine.extensions.LayoutOptions);
  }
});
