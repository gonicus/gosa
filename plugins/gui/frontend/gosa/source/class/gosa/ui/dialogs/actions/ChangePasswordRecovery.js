/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.dialogs.actions.ChangePasswordRecovery", {
  extend : gosa.ui.dialogs.PasswordRecovery,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function(step, data) {
    this.base(arguments, "edit_answers");
  },

  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    RPC_CALLS : ["listRecoveryQuestions", "requestPasswordReset"]
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {

    /**
     * Handle OK button press
     */
    _onOk: function() {
      if (this._form.validate()) {
        // save
        var model = this._form.getModel();

      }
    }
  }
});
