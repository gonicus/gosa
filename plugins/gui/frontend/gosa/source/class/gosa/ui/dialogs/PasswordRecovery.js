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
  construct : function() {
    this.base(arguments, this.tr("Password recovery"));
    this.__initForm();
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __questions: null,

    __initForm: function() {
      // Show Subject/Message pane
      var form = new qx.ui.form.Form();
      this._form = form;

      // Add the form items
      var uid = this._uid = new qx.ui.form.TextField();
      uid.setRequired(true);
      uid.setWidth(200);

      // Add the form items
      form.add(uid, this.tr("Login ID"), null, "uid");

      // add the three selection/answer fields
      var selectBoxes = [];
      for (var i=1; i <= 3; i++) {
        var select = new qx.ui.form.SelectBox();
        select.setWidth(600);
        form.add(select, this.tr("Question %1", i), null, "question_"+i);
        selectBoxes.push(select);

        var answer = new qx.ui.form.TextField();
        form.add(answer, this.tr("Answer %1", i), null, "question_"+i);
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

      this.addElement(new gosa.ui.form.renderer.Single(form, false));

      var login = this._login = gosa.ui.base.Buttons.getButton(this.tr("Reset password"));
      this.addButton(login);

    },

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {
        case "username":
          control = new qx.ui.form.TextField();

          break;
      }

      return control || this.base(arguments, id);
    }
  }
});
