/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.dialogs.PasswordRecovery", {
  extend : gosa.ui.dialogs.Dialog,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function(step) {
    this.base(arguments, this.tr("Password recovery"));

    this._currentStep = step || "start";

    this._form = new qx.ui.form.Form();

    if (this._currentStep==="start") {
      this.__initStart();
    } else if (this._currentStep==="questions") {
      this.__initQuestions();
    }
    this.addElement(new gosa.ui.form.renderer.Single(this._form, false));

    this.__initButtons();
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    _form: null,
    _ok: null,
    _abort: null,
    __questions: null,
    _currentStep : null,

    __initStart: function() {
      // Add the form items
      var uid = this._uid = new qx.ui.form.TextField();
      uid.setRequired(true);
      uid.setWidth(200);

      // Add the form items
      this._form.add(uid, this.tr("Login ID"), null, "uid");
    },

    __initQuestions: function() {

      // add the three selection/answer fields
      var selectBoxes = [];
      for (var i=1; i <= 3; i++) {
        var select = new qx.ui.form.SelectBox();
        select.setWidth(600);
        this._form.add(select, this.tr("Question %1", i), null, "question_"+i);
        selectBoxes.push(select);

        var answer = new qx.ui.form.TextField();
        this._form.add(answer, this.tr("Answer %1", i), null, "question_"+i);
      }

      gosa.io.Rpc.getInstance().cA("listRecoveryQuestions")
      .then(function(result) {
        this.__questions = result;

        // add the three selection/answer fields
        selectBoxes.forEach(function(select) {
          var selection = Math.floor((Math.random() * result.length));
          this.__questions.forEach(function(question, idx) {
            var item = new qx.ui.form.ListItem(question);
            select.add(item);
            if (selection === idx) {
              select.setSelection([item]);
            }
          }, this);
        }, this);

      }, this);
    },

    /**
     * Handle OK button press
     */
    _onOk: function() {
      if (this._form.validate()) {
        switch (this._currentStep) {
          case "start":
            // check if username exists
            gosa.io.Rpc.getInstance().cA("requestPasswordReset", this._currentStep)
            .then(function() {
              // everything went fine => show the user further instructions

            }, this)
            .catch(gosa.ui.dialogs.Error.show, this);
            break;
        }
      }
    },

    /**
     * Handle abort button press
     */
    _onAbort: function() {
      this.close();
    },

    __initButtons: function() {
      this._ok= gosa.ui.base.Buttons.getButton(this.tr("Start new password request"));
      this.addButton(this._ok);
      this._ok.addListener("execute", this._onOk, this);

      this._abort = gosa.ui.base.Buttons.getButton(this.tr("Abort"));
      this.addButton(this._abort);
      this._abort.addListener("execute", this._onAbort, this);
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this._disposeObjects("_ok", "_abort", "_form");
  }
});
