/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Interface for ActionControllers
 */
qx.Interface.define("gosa.data.IActionController", {

  members : {

    /**
     * Allow to change the password encryption selected ot not
     *
     * @return {Boolean}
     */
    allowMethodSelection: function() {},

    /**
     * Find the current password method saved in the object.
     *
     * @return {String | null} The current password method
     */
    getPasswordMethod : function() {},

    /**
     * Set the new password.
     *
     * @param method {String} The method to store the password (e.g. "MD5")
     * @param password {String} The password to save (not encoded)
     * @return {qx.Promise}
     */
    setPassword : function(method, password) {}
  }
});
