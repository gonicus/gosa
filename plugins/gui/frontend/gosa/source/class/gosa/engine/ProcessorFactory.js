/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.engine.ProcessorFactory", {
  type : "static",

  statics : {

    /**
     * Finds the correct processor for the given jsonNode.
     *
     * @param template {Object} The (already parsed) template
     * @param context {gosa.engine.Context} The context in which the processor shall run
     */
    getProcessor : function(template, context) {
      qx.core.Assert.assertObject(template);

      if (template.hasOwnProperty("type")) {
        switch (template.type) {
          case "widget":
            return new gosa.engine.processors.WidgetProcessor(context);
          case "form":
            return new gosa.engine.processors.FormProcessor(context);
        }
      }
      return null;
    }
  }
});
