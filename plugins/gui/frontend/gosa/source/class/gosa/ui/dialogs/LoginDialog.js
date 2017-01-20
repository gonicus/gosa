/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * @ignore(gosa.LocalConfig,gosa.LocalConfig.autologin,gosa.LocalConfig.user,gosa.LocalConfig.password,u2f.sign)
 */
qx.Class.define("gosa.ui.dialogs.LoginDialog",
{
  extend : gosa.ui.dialogs.Dialog,

  construct : function()
  {
    this.base(arguments, "GOsa");
    this.__initLoginForm();
    this.__initOtpForm();
    this.setFocusOrder([this._uid, this._password, this._login, this._key, this._login]);

    var controller = new qx.data.controller.Form(null, this._form);
    this._model = controller.createModel();
  },

  properties : {
    //overridden
    appearance: {
      refine: true,
      init: "login-dialog"
    }
  },

  events: {
    "login": "qx.event.type.Data"
  },

  members: {
    _uid : null,
    _password: null,
    _login: null,
    _info: null,
    _key: null,
    _mode: "login",
    __timeFormat: null,

    __initLoginForm: function() {
      // Show Subject/Message pane
      var form = new qx.ui.form.Form();
      this._form = form;

      // Add the form items
      var uid = this._uid = new qx.ui.form.TextField();
      uid.setRequired(true);
      uid.setWidth(200);

      // Add the form items
      var password = this._password = new qx.ui.form.PasswordField();
      password.setLiveUpdate(true);
      password.setRequired(true);
      password.setWidth(200);

      form.add(uid, this.tr("Login ID"), null, "uid");
      form.add(password, this.tr("Password"), null, "password");

      this.addElement(new gosa.ui.form.renderer.Single(form, false));

      // Add status label
      var info = this._info = new qx.ui.basic.Label();
      info.setRich(true);
      info.exclude();
      this.addAt(info, 0);
      this.getLayout().setAlignX("center");

      var login = this._login = gosa.ui.base.Buttons.getButton(this.tr("Login"));
      this.addButton(login);

      login.addListener("execute", function(){
        if (this._form.validate()) {

          if (gosa.Config.notifications) {
            if (gosa.Config.notifications.checkPermission() != 0) {
              gosa.Config.notifications.requestPermission();
            }
          }

          var rpc = gosa.io.Rpc.getInstance();
          if (this._mode === "login") {
            rpc.callAsync(this._handleAuthentification.bind(this), "login", this._model.get("uid"), this._model.get("password"));
          } else if (this._mode === "verify") {
            rpc.callAsync(this._handleAuthentification.bind(this), "verify", this._model.get("key"));
          }
        }
      }, this);

      // Automatically fill in username and password if wanted
      if(gosa.LocalConfig && gosa.LocalConfig.autologin){
        uid.setValue(gosa.LocalConfig.user);
        password.setValue(gosa.LocalConfig.password);
        login.execute();
      }
    },

    __initOtpForm: function() {
      var key = this._key = new qx.ui.form.TextField();
      key.setWidth(200);
      key.exclude();

      this._form.add(key, this.tr("OTP-Passkey"), null, "key");
    },

    /**
     * Callback function for RPC login responses
     *
     * @param result {Number} One of gosa.Config.AUTH_*
     * @param error {Object} Error as sent by the backend
     * @protected
     */
    _handleAuthentification: function(result, error) {

      if (error) {
        new gosa.ui.dialogs.Error(error).open();
        return;
      }

      var lockForm = function(hint, time, doCountdown) {
        var message = hint;
        this._info.setTextColor("red");
        this._info.show();
        this._password.setEnabled(false);
        this._uid.setEnabled(false);
        this._login.setEnabled(false);
        this._key.setEnabled(false);

        var timer = null;

        if (doCountdown === true) {
          var end = Date.now() + time;
          message += "<br/>" + this.tr("Your login is locked for %1 seconds", lease);
          timer = qx.util.TimerManager.getInstance().start(function() {
            lease = Math.round((end-Date.now())/1000);
            this._info.setValue(hint + "<br/>" + this.tr("Your login is locked for %1 seconds", lease));
          }, 1000, this);
        }
        this._info.setValue(message);

        qx.event.Timer.once(function() {
          this._uid.focus();
          this._uid.setValue("");
          this._password.setValue("");
          this._password.setEnabled(true);
          this._uid.setEnabled(true);
          this._login.setEnabled(true);
          this._info.setValue("");
          this._info.resetTextColor();
          this._info.exclude();
          this._key.setValue("");
          this._key.setEnabled(true);
          if (timer) {
            qx.util.TimerManager.getInstance().stop(timer);
            timer = null;
          }
        }, this, time || 4000);
      }.bind(this);

      var state = parseInt(result.state);
      switch (state) {
        case gosa.Config.AUTH_FAILED:
          lockForm(this.tr("Invalid login..."));
          break;

        case gosa.Config.AUTH_LOCKED:
          var lockTime = parseInt(result.seconds);
          var lease = Math.ceil(lockTime-Date.now()/1000);
          lockForm(this.tr("Invalid login..."), lease*1000, true);
          break;

        case gosa.Config.AUTH_SUCCESS:
          this.fireDataEvent("login", { user : this._model.get("uid") });
          this.close();
          break;

        case gosa.Config.AUTH_OTP_REQUIRED:
          this._uid.exclude();
          this._password.exclude();
          this._key.show();
          this._key.focus();
          this._mode = "verify";
          break;

        case gosa.Config.AUTH_U2F_REQUIRED:
          var rpc = gosa.io.Rpc.getInstance();
          var data = qx.lang.Json.parse(result.u2f_data);
          var dialog = new gosa.ui.dialogs.U2FInfo();
          dialog.show();
          u2f.sign(data.authenticateRequests[0]['appId'], data.registerRequests, data.authenticateRequests, function(deviceResponse) {
            dialog.close();
            if (deviceResponse.errorCode) {
              this._info.setValue('<span style="color:red">' + this.tr("Device responded with error '%1': %2", deviceResponse.errorCode, gosa.Tools.getU2FErrorMessage(deviceResponse.errorCode)) + '</span>');
              this._info.show();
            } else {
              rpc.callAsync(this._handleAuthentification.bind(this), "verify", qx.lang.Json.stringify(deviceResponse));
            }
          }.bind(this));
          break;

      }
    }
  },

  destruct : function() {
    this._disposeObjects("_uid", "_password", "_login", "_info", "_key");
  }
});

