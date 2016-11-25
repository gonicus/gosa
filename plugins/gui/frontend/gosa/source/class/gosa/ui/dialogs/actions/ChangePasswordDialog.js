/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */
qx.Class.define("gosa.ui.dialogs.actions.ChangePasswordDialog", {

  extend: gosa.ui.dialogs.actions.Base,

  construct: function(actionController) {
    this.base(arguments, actionController, this.tr("Change password..."), gosa.Config.getImagePath("status/dialog-password.png", 22));

    this._initWidgets();
  },

  statics : {
    RPC_CALLS : ["listPasswordMethods", "setUserPassword"]
  },

  members : {

    _initWidgets : function() {
      var form = this._form = new qx.ui.form.Form();

      // current password method
      var current = this._actionController.getPasswordMethod();

      var method = new qx.ui.form.SelectBox();
      gosa.io.Rpc.getInstance().cA("listPasswordMethods")
      .then(function(result) {
        for (var item in result) {
          var tempItem = new qx.ui.form.ListItem(result[item], null, result[item]);
          method.add(tempItem);

          if (current == result[item]) {
            method.setSelection([tempItem]);
          }
        }
      }, this)
      .catch(function(error) {
        new gosa.ui.dialogs.Error(error.message).open();
        this.close();
      }, this);

      // Add the form items
      var pwd1 = new qx.ui.form.PasswordField();
      pwd1.setRequired(true);
      pwd1.setWidth(200);

      var pwd2 = new qx.ui.form.PasswordField();
      pwd2.setRequired(true);
      pwd2.setWidth(200);

      form.add(method, this.tr("Encryption"), null, "method");
      form.add(pwd1, this.tr("New password"), null, "pwd1");
      form.add(pwd2, this.tr("New password (repeated)"), null, "pwd2");

      var la = new gosa.ui.form.renderer.Single(form);
      la.getLayout().setColumnAlign(0, "left", "middle");
      this.addElement(la);
      var controller = new qx.data.controller.Form(null, form);

      // Add password indicator
      this._passwordIndicator = new qx.ui.indicator.ProgressBar();
      this._passwordIndicator.setDecorator(null);
      this._passwordIndicator.setHeight(5);
      this._passwordIndicator.setBackgroundColor("background-selected-disabled");
      this.addElement(this._passwordIndicator);

      // Add status label
      this._info = new qx.ui.basic.Label();
      this._info.setRich(true);
      this._info.exclude();
      this.addElement(this._info);
      this.getLayout().setAlignX("center");

      // Wire status label
      pwd1.addListener("keyup", this.updateStatus, this);
      pwd2.addListener("keyup", this.updateStatus, this);
      this._pwd1 = pwd1;
      this._pwd2 = pwd2;

      this._model = controller.createModel();

      var ok = gosa.ui.base.Buttons.getButton(this.tr("Set password"), "status/dialog-password.png");
      ok.addState("default");
      ok.addListener("execute", this.setPassword, this);
      ok.setEnabled(false);
      this._ok = ok;

      var cancel = gosa.ui.base.Buttons.getCancelButton();
      cancel.addState("default");
      cancel.addListener("execute", this.close, this);

      this.addButton(ok);
      this.addButton(cancel);

      this.setFocusOrder([pwd1, pwd2, ok]);
    },

    updateStatus : function()
    {
      // Set password strength
      var score = this.getPasswordScore(this._pwd1.getValue());
      this._passwordIndicator.setValue(score);
      if (score < 25) {
        this._passwordIndicator.getChildControl("progress").setBackgroundColor("red");
      } else if (score < 50) {
        this._passwordIndicator.getChildControl("progress").setBackgroundColor("orange");
      } else if (score < 75) {
        this._passwordIndicator.getChildControl("progress").setBackgroundColor("yellow");
      } else {
        this._passwordIndicator.getChildControl("progress").setBackgroundColor("green");
      }

      if (this._pwd1.getValue() == this._pwd2.getValue()) {
        this._info.setValue("");
        this._info.exclude();
        this._ok.setEnabled(this._pwd1.getValue() === ""?false:true);
      } else {
        this._info.setValue("<span style='color:red'>" + this.tr("Passwords do not match!") + "</span>");
        this._info.show();
        this._ok.setEnabled(false);
      }
    },

    setPassword : function()
    {
      if (this._form.validate()) {
        if (this._model.get("pwd1") != this._model.get("pwd2")) {
            return;
        }

        this._actionController.setPassword(this._model.get("method"), this._model.get("pwd1"))
        .then(function() {
          this.close();
          new gosa.ui.dialogs.Info(this.tr("Password has been changed successfully.")).open();
        }, this)
        .catch(function(error) {
          new gosa.ui.dialogs.Error(error.message).open();
        });
      }
    },

    /*************************************************************
    Created: 20060120
    Author:  Steve Moitozo <god at zilla dot us>
    Description: This is a quick and dirty password quality meter
                     written in JavaScript
    License: MIT License (see below)
    =================================
    Revision Author: Dick Ervasti (dick dot ervasti at quty dot com)
    Revision Description: Exchanged text based prompts for a graphic thermometer
    =================================
    Revision Author: Jay Bigam jayb <o> tearupyourlawn <o> com
    Revision Date: Feb. 26, 2007
    Revision Description: Changed D. Ervasti's table based "thermometer" to CSS.
    Revision Notes: - Verified to work in FF2, IE7 and Safari2
                    - Modified messages to reflect Minimum strength requirement
                    - Added formSubmit button disabled until minimum requirement met
    =================================
    Modified: 20061111 - Steve Moitozo corrected regex for letters and numbers
                         Thanks to Zack Smith -- zacksmithdesign.com
                         and put MIT License back in
    Modified: 20100201 - Cajus Pollmeier stripped parts unnessesary for GOsa and
                         moved to prototype. Stripped comments.
    Modified: 20120820 - Cajus Pollmeier stripped everything but the strength
                         calculation to make it usable for qooxdoo widgets.
    ---------------------------------------------------------------
    Copyright (c) 2006 Steve Moitozo <god at zilla dot us>

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or
    sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall
    be included in all copies or substantial portions of the
    Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
    KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
    WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
    AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
    OR OTHER DEALINGS IN THE SOFTWARE.
    ---------------------------------------------------------------

    ************************************************************ */
    getPasswordScore : function (passwd)
    {
      if (passwd === null) {
        passwd = "";
      }
      var score = 0;

      // PASSWORD LENGTH
      if (passwd.length === 0 || !passwd.length)      // length 0
      {
          score = -1;
      }
      else if (passwd.length>0 && passwd.length<5) // length between 1 and 4
      {
          score += 3;
      }
      else if (passwd.length>4 && passwd.length<8) // length between 5 and 7
      {
          score += 6;
      }
      else if (passwd.length>7 && passwd.length<12)// length between 8 and 15
      {
          score += 12;
      }
      else if (passwd.length>11)                   // length 16 or more
      {
          score += 18;
      }

      // LETTERS (Not exactly implemented as dictacted above because of my limited understanding of Regex)
      if (passwd.match(/[a-z]/))                   // [verified] at least one lower case letter
      {
          score += 1;
      }

      if (passwd.match(/[A-Z]/))                   // [verified] at least one upper case letter
      {
          score += 5;
      }

      // NUMBERS
      if (passwd.match(/\d+/))                     // [verified] at least one number
      {
          score += 5;
      }

      if (passwd.match(/(.*[0-9].*[0-9].*[0-9])/)) // [verified] at least three numbers
      {
          score += 5;
      }

      // SPECIAL CHAR
      if (passwd.match(/.[!,@,#,$,%,^,&,*,?,_,~]/))// [verified] at least one special character
      {
          score += 5;
      }

      // [verified] at least two special characters
      if (passwd.match(/(.*[!,@,#,$,%,^,&,*,?,_,~].*[!,@,#,$,%,^,&,*,?,_,~])/))
      {
          score += 5;
      }

      // COMBOS
      if (passwd.match(/([a-z].*[A-Z])|([A-Z].*[a-z])/))        // [verified] both upper and lower case
      {
          score += 2;
      }

      if (passwd.match(/([a-zA-Z])/) && passwd.match(/([0-9])/)) // [verified] both letters and numbers
      {
          score += 2;
      }

      // [verified] letters, numbers, and special characters
      if (passwd.match(/([a-zA-Z0-9].*[!,@,#,$,%,^,&,*,?,_,~])|([!,@,#,$,%,^,&,*,?,_,~].*[a-zA-Z0-9])/))
      {
          score += 2;
      }

      // Fit into range
      if (score < 0) {
        score = 0;
      }
      if (score > 46) {
        score = 46;
      }

      return Math.floor(score * 100 / 46);
    }

  }

});
