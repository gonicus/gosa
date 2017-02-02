/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Somplified controller for actions that can be done on a user object without being logged in (e.g. change password
 * after the recovery process has been succeeded)
 */
qx.Class.define("gosa.data.RecoveryActionController", {
  extend : qx.core.Object,
  implement: gosa.data.IActionController,

  construct : function(uid, uuid) {
    this.base(arguments);
    this._uuid = uuid;
    this._uid = uid;
  },

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events : {
    "changeSuccessful": "qx.event.type.Data"
  },

  members : {

    // overridden
    allowMethodSelection: function() {
      return false;
    },

    /**
     * Find the current password method saved in the object.
     *
     * @return {String | null} The current password method
     */
    getPasswordMethod : function() {
      return null;
    },

    /**
     * Set the new password.
     *
     * @param password {String} The password to save (not encoded)
     * @return {qx.Promise}
     */
    setPassword : function(password) {
      qx.core.Assert.assertString(password);
      return gosa.io.Rpc.getInstance().cA("requestPasswordReset", this._uid, "change_password", this._uuid, password)
      .then(function(result) {
        this.fireDataEvent("changeSuccessful", result);
      }, this)
      .catch(function(error) {
        gosa.ui.dialogs.Error.show(error);
        this.fireDataEvent("changeSuccessful", false);
      }, this)
    }
  }
});
