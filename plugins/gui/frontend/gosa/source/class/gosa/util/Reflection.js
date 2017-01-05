/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.util.Reflection", {
  type : "static",

  statics : {
    getPackageName: function(item) {
      var className = "";
      if (qx.lang.Type.isObject(item)) {
        className = item.constructor.classname;
      } else if (item.$$type == "Class") {
        className = item.classname;
      }
      if (className.length > 0) {
        var parts = className.split("."); parts.pop();
        return parts.join(".");
      }
      return null;
    }
  }
});
