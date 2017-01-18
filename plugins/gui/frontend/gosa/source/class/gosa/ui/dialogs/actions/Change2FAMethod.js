/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* @ignore(u2f.register)
* Dialog for changing the two-factor authentification.
*/
qx.Class.define("gosa.ui.dialogs.actions.Change2FAMethod", {

  extend: gosa.ui.dialogs.actions.Base,

  statics : {
    RPC_CALLS : [
      "setTwoFactorMethod",
      "getTwoFactorMethod",
      "getAvailable2FAMethods",
      "completeU2FRegistration"
    ]
  },

  construct: function(actionController) {
    this.base(arguments, actionController, this.tr("Change 2FA method"));
    this._initWidgets();
  },

  members : {
    _ok : null,
    _cancel : null,
    _current: null,
    _pwd : null,
    _method : null,
    _qrCodeField : null,

    _initWidgets : function() {
      // Show Subject/Message pane
      var form = new qx.ui.form.Form();
      this._form = form;

      var method = this._method = new qx.ui.form.SelectBox();
      method.setWidth(200);

      this._actionController.getTwoFactorMethod()
      .then(function(response) {
        this._current = response;
        // show password field if the user wants to change the 2FA method
        method.addListener("changeSelection", function(e) {
          var selected = e.getData()[0].getModel();
          if (this._current === null || this._current === selected) {
            // if we have no 2FA activated at the moment we do not need to check the user pwd
            this._pwd.exclude();
            this._pwd.setRequired(false);
          } else {
            this._pwd.show();
            this._pwd.setRequired(true);
          }
        }, this);
      }, this);

      var rpc = gosa.io.Rpc.getInstance();
      rpc.cA("getAvailable2FAMethods")
      .then(function(result) {
        for (var item in result) {
          var label = result[item];
          if (!label) {
            label = this.tr("Disabled");
          }
          var tempItem = new qx.ui.form.ListItem(label, null, result[item]);
          method.add(tempItem);

          if(this._current == result[item]){
            method.setSelection([tempItem]);
          }
        }
      }, this)
      .catch(function(error) {
        new gosa.ui.dialogs.Error(error).open();
        this.close();
      }, this);

      // Add the form items
      var pwd = this._pwd = new qx.ui.form.PasswordField();
      pwd.setWidth(200);

      form.add(method, this.tr("Select method"), null, "method");
      form.add(pwd, this.tr("Verify with password"), null, "pwd");

      var la = new gosa.ui.form.renderer.Single(form);
      la.getLayout().setColumnAlign(0, "left", "middle");
      this.addElement(la);
      var controller = new qx.data.controller.Form(null, form);

      // Add status label
      this._info = new gosa.ui.basic.StatusLabel();
      this._info.exclude();
      this.addElement(this._info);
      this.getLayout().setAlignX("center");

      // QR-Code field
      this._qrCodeField = new qx.ui.container.Composite(new qx.ui.layout.VBox());
      this._qrCodeField.exclude();
      this.addElement(this._qrCodeField);

      this._model = controller.createModel();

      var ok = this._ok = gosa.ui.base.Buttons.getButton(this.tr("Change method"), "@Ligature/umbrella/22");
      ok.setAppearance("button-primary");
      ok.addState("default");
      ok.addListener("execute", this._setMethod, this);

      var cancel = this._cancel = gosa.ui.base.Buttons.getCancelButton();
      cancel.addState("default");
      cancel.addListener("execute", this.close, this);

      this.addButton(ok);
      this.addButton(cancel);

      this.setFocusOrder([method, pwd, ok]);

    },

    _setMethod : function() {
      if (this._form.validate()) {
        var method = this._method.getSelection()[0].getModel();
        if (method !== this._current) {
          if (this._current === null) {
            // no confirmation required
            this._actionController.setTwoFactorMethod(method)
            .then(this._handleMethodChangeResponse, this)
            .catch(function(exc) {
              this._showInfo(null, exc.getData().message);
            }, this);
          } else {
            var pwd = this._pwd.getValue();
            this._actionController.setTwoFactorMethod(method, pwd)
            .then(this._handleMethodChangeResponse, this)
            .catch(function(exc) {
              this._showInfo(null, exc.getData().message);
            }, this);
          }
        }
        else {
          // nothing to do, just close this dialog
          this.close();
        }
      }
    },

    _handleMethodChangeResponse : function(result, error) {
      if (error) {
        this._showInfo(null, error.message);
      } else {
        if (result) {
          if (qx.lang.Type.isString(result) && result.startsWith("otpauth://")) {
            // generate and show QR-Code
            this._showQrCode(result);
            this._showInfo(result);
            this._ok.exclude();
            this._cancel.setLabel(this.tr("Close"));
          } else if (result === "true") {
            this.close();
          } else {
            try {
              var data = qx.lang.Json.parse(result);
              var dialog = new gosa.ui.dialogs.U2FInfo();
              dialog.show();
              u2f.register(data.registerRequests[0].appId, data.registerRequests, data.authenticateRequests, function(deviceResponse) {
                dialog.close();
                if (deviceResponse.errorCode) {
                  this._showInfo(null, this.tr("Device responded with error '%1': %2", deviceResponse.errorCode, gosa.Tools.getU2FErrorMessage(deviceResponse.errorCode)));
                } else {
                  this._actionController.finishU2FRegistration(qx.lang.Json.stringify(deviceResponse)).then(this._handleMethodChangeResponse, this);
                }
              }.bind(this));
            } catch (e) {
              console.error(e);
            }

          }
        } else {
          this._showQrCode(null);
          this.close();
        }
      }
    },

    _showQrCode : function(data) {
      this._qrCodeField.removeAll();
      if (data) {
        this._qrCodeField.add(new gosa.ui.QrCode(data, 316));
        this._qrCodeField.show();
      } else {
        this._qrCodeField.exclude();
      }
    },

    _showInfo : function(message, error) {
      if (!error) {
        this._info.removeState("error");
        this._info.setValue(message);
        this._info.exclude();
      } else {
        this._info.addState("error");
        this._info.setValue(error);
        this._info.show();
      }
    }
  },

  destruct: function() {
    this._disposeObjects("_pwd", "_method", "_qrCodeField", "_ok", "_cancel");
  }
});
