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

qx.Class.define("gosa.ui.dialogs.actions.ChangePasswordRecovery", {
  extend : gosa.ui.dialogs.PasswordRecovery,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function(actionController) {
    this.base(arguments, "edit_answers");

    this._actionController = actionController;

    // TODO: retrieve amount of questions from user policy
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
        var model = this._controller.createModel();
        // save
        var result = {};
        for (var i=1; i <= this.getTotalQuestions(); i++) {
          var question = model["getQuestion"+i]();
          result[this._questions.indexOf(question)] = model["getAnswer"+i]();
        }
        this._actionController.changePasswordRecoveryAnswers(qx.lang.Json.stringify(result))
        .then(function() {
          this.close();
        }, this)
        .catch(gosa.ui.dialogs.Error.show);
      }
    }
  }
});
