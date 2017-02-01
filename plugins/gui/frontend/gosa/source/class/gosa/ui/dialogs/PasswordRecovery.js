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
  construct : function(step, data) {
    this.base(arguments, this.tr("Password recovery"));

    this._currentStep = step || "start";
    this._data = data;

    this._form = new qx.ui.form.Form();
    this.__initButtons();

    if (this._currentStep==="start") {
      this.__initStart();
    } else if (this._currentStep==="questions" || this._currentStep==="edit_answers") {
      this.__initQuestions();
    }
    this.addElement(this._createFormRenderer());
    this._controller = new qx.data.controller.Form(null, this._form);
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    totalQuestions: {
      check: "Number",
      init: 7
    },
    requiredCorrectAnswers: {
      check: "Number",
      init: 3
    }
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
    _questions: null,
    _currentStep : null,
    _answerModelPaths: null,
    _controller: null,

    _createFormRenderer: function() {
      if (this._currentStep === "questions") {
        return new gosa.ui.form.renderer.LabelAbove(this._form, false);
      } else {
        return new gosa.ui.form.renderer.Single(this._form, false);
      }
    },

    __initStart: function() {

      this._ok.setLabel(this.tr("Start new password request"));
      // Add the form items
      var uid = this._uid = new qx.ui.form.TextField();
      uid.setRequired(true);
      uid.setWidth(200);

      // Add the form items
      this._form.add(uid, this.tr("Login ID"), null, "uid");
    },

    __initQuestions: function() {
      // add the selection/answer fields
      var selectBoxes = [];
      var selectionControllers = new qx.data.Array();

      if (this._currentStep==="edit_answers" ) {
        this._ok.setLabel(this.tr("Save"));

        for (var i=1; i <= this.getTotalQuestions(); i++) {
          var select = new qx.ui.form.SelectBox();
          selectionControllers.push(new qx.data.controller.List(null, select, ""));
          select.setWidth(600);
          this._form.add(select, this.tr("Question %1", i), null, "question"+i);
          selectBoxes.push(select);

          var answer = new qx.ui.form.TextField();
          answer.setRequired(true);
          this._form.add(answer, this.tr("Answer %1", i), null, "answer"+i);
        }

        gosa.io.Rpc.getInstance().cA("listRecoveryQuestions")
        .then(function(result) {
          this._questions = result;

          // add the selection/answer fields
          selectBoxes.forEach(function(select, idx) {
            selectionControllers.getItem(idx).setModel(new qx.data.Array(this._questions));
          }, this);
        }, this)
        .catch(gosa.ui.dialogs.Error.show, this);
      } else {
        this._ok.setLabel(this.tr("Send"));

        qx.Promise.all([
          gosa.io.Rpc.getInstance().cA("requestPasswordReset", this._data.uid, "get_questions", this._data.uuid),
          gosa.io.Rpc.getInstance().cA("listRecoveryQuestions")
          ])
        .spread(function(selectedQuestions, questions) {
          this._questions = questions;
          this._selectedQuestions = selectedQuestions;
          for (var i=0; i < selectedQuestions.length; i++) {
            var answer = new qx.ui.form.TextField();
            answer.setRequired(true);
            this._form.add(answer, questions[selectedQuestions[i]], null, "answer" + selectedQuestions[i]);
          }
          this.center();
        }, this)
        .catch(gosa.ui.dialogs.Error.show, this);
      }
    },

    /**
     * Handle OK button press
     */
    _onOk: function() {
      if (this._form.validate()) {
        var model = this._controller.createModel();
        switch (this._currentStep) {
          case "start":
            // check if username exists
            gosa.io.Rpc.getInstance().cA("requestPasswordReset", this._uid.getValue(), null, this._currentStep)
            .then(function() {
              // TODO show the user further instructions
              console.log("all fine");
            }, this)
            .catch(gosa.ui.dialogs.Error.show, this);
            break;

          case "questions":
            var result = {};
            this._selectedQuestions.forEach(function(idx) {
              result[idx] = model.get("answer"+idx);
            }, this);
            console.log(result);
            gosa.io.Rpc.getInstance().cA("requestPasswordReset", this._data.uid, "check_answers", this._data.uuid, qx.lang.Json.stringify(result))
            .then(function(result) {
              if (result === true) {
                // open change password dialog
                var actionController = new gosa.data.RecoveryActionController(this._data.uid, this._data.uuid);
                var dialog = new gosa.ui.dialogs.actions.ChangePasswordDialog(actionController);
                dialog.open();
              } else {
                // at least one answer must have been wrong

              }
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
      this._ok = gosa.ui.base.Buttons.getButton(this.tr("Start new password request"));
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
    this._disposeObjects("_ok", "_abort", "_form", "_controller");
  }
});
