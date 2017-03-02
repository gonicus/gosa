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

qx.Class.define("gosa.engine.extensions.ValueInjector", {
  extend: qx.core.Object,

  implement : [gosa.engine.extensions.IExtension],

  members : {

    process : function(data, target, context) {
      var obj = context.getObject();
      var labelsAndValues = data.map(function(entry) {
        return {
          label : entry.label,
          value : obj.get(entry.modelPath)
        };
      }, this);

      target.setLabelsAndValues(labelsAndValues);
    }
  },

  defer : function() {
    gosa.engine.ExtensionManager.getInstance().registerExtension("valueInjector", gosa.engine.extensions.ValueInjector);
  }
});
