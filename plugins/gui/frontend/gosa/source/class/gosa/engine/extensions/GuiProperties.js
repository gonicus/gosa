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
