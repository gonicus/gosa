/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * @ignore(gosa.LocalConfig,gosa.LocalConfig.autologin,gosa.LocalConfig.user,gosa.LocalConfig.password)
 */
qx.Class.define("gosa.ui.dialogs.LoginDialog",
{
  extend : gosa.ui.dialogs.Dialog,

  construct : function()
  {
    this.base(arguments, this.tr("Login"));
    this.__init();
  },

  events: {
    "login": "qx.event.type.Data"
  },

  members: {
    _uid : null,
    _password: null,
    _login: null,
    _info: null,

    __init: function() {
      // Show Subject/Message pane
      var form = new qx.ui.form.Form();
      this._form = form;

      // Add the form items
      var uid = this._uid = new qx.ui.form.TextField();
      uid.setRequired(true);
      uid.setWidth(200);

      // Add the form items
      var password = this._password = new qx.ui.form.PasswordField();
      password.setRequired(true);
      password.setWidth(200);

      form.add(uid, this.tr("Login ID"), null, "uid");
      form.add(password, this.tr("Password"), null, "password");

      this.addElement(new gosa.ui.form.renderer.Single(form, false));

      var controller = new qx.data.controller.Form(null, form);
      this._model = controller.createModel();

      // Add status label
      var info = this._info = new qx.ui.basic.Label();
      info.setRich(true);
      info.exclude();
      this.addElement(info);
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
          rpc.callAsync(this._handleAuthentification.bind(this), "login", this._model.get("uid"), this._model.get("password"));
        }
      }, this);

      this.setFocusOrder([uid, password, login]);

      // Automatically fill in username and password if wanted
      if(gosa.LocalConfig && gosa.LocalConfig.autologin){
        uid.setValue(gosa.LocalConfig.user);
        password.setValue(gosa.LocalConfig.password);
        login.execute();
      }
    },

    /**
     * Callback function for RPC login responses
     *
     * @param result {Number} One of gosa.Config.AUTH_*
     * @param error
     * @protected
     */
    _handleAuthentification: function(result, error) {
      switch (parseInt(result)) {
        case gosa.Config.AUTH_FAILED:
          info.setValue('<span style="color:red">' + this.tr("Invalid login...") + '</span>');
          info.show();
          this._password.setEnabled(false);
          this._uid.setEnabled(false);
          this._login.setEnabled(false);

          var timer = qx.util.TimerManager.getInstance();
          timer.start(function(userData, timerId) {
            this._uid.focus();
            this._uid.setValue("");
            this._password.setValue("");
            this._password.setEnabled(true);
            this._uid.setEnabled(true);
            this._login.setEnabled(true);
            this._info.setValue("");
            this._info.exclude();
          }, 0, this, null, 4000);
          break;

        case gosa.Config.AUTH_SUCCESS:
          this.fireDataEvent("login", { user : this._model.get("uid") });
          this.close();
          break;

        case gosa.Config.AUTH_OTP_REQUIRED:
          // TODO: handle OTP authentification
          break;

        case gosa.Config.AUTH_U2F_REQUIRED:
          // TODO: handle U2F authentification
          break;

      }
    }
  },

  destruct : function() {
    this._disposeObjects("_uid", "_password", "_login", "_info");
  }
});

