/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.util.Object", {
  type : "static",

  statics : {

    /**
     * Iterates over a javascript object/map and call the callback function on each iteration.
     *
     * @param object {Object}
     * @param callback {Function} Function that is invoked with the parameters key and value
     * @param context {Object ? null} Optional context for the callback
     */
    iterate: function(object, callback, context) {
      qx.core.Assert.assertMap(object);
      qx.core.Assert.assertFunction(callback);

      for (var key in object) {
        if (object.hasOwnProperty(key)) {
          callback.call(context, key, object[key]);
        }
      }
    }
  }
});
