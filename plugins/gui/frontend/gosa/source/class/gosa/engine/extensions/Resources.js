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
