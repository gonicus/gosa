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

    this._info = new qx.ui.basic.Label();
    this._info.set({
      rich: true,
      wrap: true,
      padding: 10
    });
    this._info.exclude();
    this.addElement(this._info);

    if (this._currentStep==="start") {
      this.__initStart();
    } else if (this._currentStep==="questions" || this._currentStep==="edit_answers") {
      this.__initQuestions();
    }


    this.addElement(this._createFormRenderer());
    this._controller = new qx.data.controller.Form(null, this._form);
    this._form.getValidationManager().setValidator(this.__validateForm.bind(this));
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
    _info: null,
    _form: null,
    _ok: null,
    _abort: null,
    _questions: null,
    _currentStep : null,
    _answerModelPaths: null,
    _controller: null,
    _formRenderer: null,

    _createFormRenderer: function() {
      if (!this._formRenderer) {
        if (this._currentStep === "questions") {
          this._formRenderer = new gosa.ui.form.renderer.LabelAbove(this._form, false);
        }
        else {
          this._formRenderer = new gosa.ui.form.renderer.Single(this._form, false);
        }
      }
      return this._formRenderer;
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
      var selectBoxes = this._selectBoxes = [];
      var selectionControllers = new qx.data.Array();

      if (this._currentStep==="edit_answers" ) {
        this._ok.setLabel(this.tr("Save"));
        this.showInfo(this.tr("Please select %1 different questions and answer them.", this.getTotalQuestions()));

        for (var i=1; i <= this.getTotalQuestions(); i++) {
          var select = new qx.ui.form.SelectBox();
          selectionControllers.push(new qx.data.controller.List(null, select, ""));
          select.setWidth(600);
          this._form.add(select, this.tr("Question %1", i), null, "question"+i);
          selectBoxes.push(select);

          var answer = new qx.ui.form.TextField();
          answer.setRequired(true);
          answer.setInvalidMessage(this.tr("Invalid answer."));
          this._form.add(answer, this.tr("Answer %1", i), qx.lang.Function.curry(this.__validateAnswer.bind(this), i-1), "answer"+i);
        }

        gosa.io.Rpc.getInstance().cA("listRecoveryQuestions")
        .then(function(result) {
          this._questions = result;

          // add the selection/answer fields
          selectBoxes.forEach(function(select, idx) {
            selectionControllers.getItem(idx).setModel(new qx.data.Array(this._questions));
          }, this);
        }, this)
        .catch(this.__handleRpcError, this);
      } else {
        this._ok.setLabel(this.tr("Send"));
        this.showInfo(this.tr("Please answer your recovery questions to proceed."));

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
        .catch(this.__handleRpcError, this);
      }
    },

    /**
     * Validate the complete form
     */
    __validateForm: function() {
      // check for duplicate questions
      var selectedQuestions = [];
      this._selectBoxes.forEach(function(box) {
        var question = box.getModelSelection().getItem(0);
        if (selectedQuestions.indexOf(question) >= 0) {
          box.setValid(false);
          box.setInvalidMessage(this.tr("Please avoid duplicate questions."))
        } else {
          selectedQuestions.push(question);
        }
      }, this);
    },

    /**
     * Validate an answer field
     * @param idx {Number} answer index
     * @param value {String} current field content
     * @return {Boolean} True if the answer is valid
     */
    __validateAnswer: function(idx, value) {
      if (!value) {
        return false;
      }
      var cleanedValue = value.replace(/[\W]+/gi, "");
      if (cleanedValue.length === 0) {
        return false;
      }

      // check that the user did not use the given example
      var question = this._selectBoxes[idx].getModelSelection().getItem(0);
      var example = question.match(/.+\((.+)\)\s*\??$/);
      if (!example || example.length < 2) {
        return true;
      }
      return (example[1].replace(/[\W]+/gi, "").indexOf(cleanedValue) === -1);
    },

    __handleRpcError: function(error) {
      this.error(error);
      this.showError(error.getData().message);
      this._ok.setEnabled(false);
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
            gosa.io.Rpc.getInstance().cA("requestPasswordReset", this._uid.getValue(), this._currentStep)
            .then(function() {
              this.showInfo(this.tr("An e-mail has been send to your account. Please follow the instructions in this mail. You can close this window now."));
              this._formRenderer.exclude();
              this._buttonPane.exclude();
              this.center();
            }, this)
            .catch(this.__handleRpcError, this);
            break;

          case "questions":
            var result = {};
            this._selectedQuestions.forEach(function(idx) {
              result[idx] = model.get("answer"+idx);
            }, this);
            gosa.io.Rpc.getInstance().cA("requestPasswordReset", this._data.uid, "check_answers", this._data.uuid, qx.lang.Json.stringify(result))
            .then(function(result) {
              if (result === true) {
                // open change password dialog
                var actionController = new gosa.data.controller.RecoveryAction(this._data.uid, this._data.uuid);
                actionController.addListener("changeSuccessful", function(ev) {
                  if (ev.getData() === true) {
                    this.close();
                  } else {
                    // do not close this dialog, error
                  }
                }, this);
                var dialog = new gosa.ui.dialogs.actions.ChangePasswordDialog(actionController);
                dialog.open();
                this.hideInfo();
              } else {
                // at least one answer must have been wrong
                this.showError(this.tr("At least one answer is wrong, please try again. You can reload this window to receive other questions."));
                this.center();
              }
            }, this)
            .catch(this.__handleRpcError, this);
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
    },

    showError: function(message) {
      this._info.show();
      this._info.setTextColor("error-text");
      this._info.setValue(message);
    },

    showInfo: function(message) {
      this._info.show();
      this._info.setTextColor("aqua-dark");
      this._info.setValue(message);
    },

    hideInfo: function() {
      this._info.exclude();
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this._disposeObjects("_ok", "_abort", "_form", "_controller", "_info");
  }
});
