qx.Class.define("gosa.ui.dialogs.LoginDialog",
{
  extend : gosa.ui.dialogs.Dialog,

  construct : function()
  {
    this.base(arguments, this.tr("Login"));

    // Show Subject/Message pane
    var form = new qx.ui.form.Form();
    this._form = form;

    // Add the form items
    var uid = new qx.ui.form.TextField();
    uid.setRequired(true);
    uid.setWidth(200);

    // Add the form items
    var password = new qx.ui.form.PasswordField();
    password.setRequired(true);
    password.setWidth(200);

    form.add(uid, this.tr("Login ID"), null, "uid");
    form.add(password, this.tr("Password"), null, "password");

    this.addElement(new gosa.ui.form.renderer.Single(form, false));
    var controller = new qx.data.controller.Form(null, form);
    this._model = controller.createModel();

    // Add status label
    var info = new qx.ui.basic.Label();
    info.setRich(true);
    info.exclude();
    this.addElement(info);
    this.getLayout().setAlignX("center");

    var login = gosa.ui.base.Buttons.getButton(this.tr("Login"));
    this.addButton(login);

    login.addListener("execute", function(){
      if (this._form.validate()) {

        if (gosa.Config.notifications) {
            if (gosa.Config.notifications.checkPermission() != 0) {
                gosa.Config.notifications.requestPermission();
          }
        }

        var rpc = gosa.io.Rpc.getInstance();
        var that = this;
        rpc.callAsync(function(result, error){
          if(!result){
            info.setValue("<span style='color:red'>" + that.tr("Invalid login ...") + "</span>");
            info.show();
            password.setEnabled(false);
            uid.setEnabled(false);
            login.setEnabled(false);
            
            var timer = qx.util.TimerManager.getInstance();
            timer.start(function(userData, timerId){
              uid.focus();
              uid.setValue("");
              password.setValue("");
              password.setEnabled(true);
              uid.setEnabled(true);
              login.setEnabled(true);
              info.setValue("");
              info.exclude();
            }, 0, this, null, 4000);

          }else{
            that.fireDataEvent("login", {user: that._model.get("uid")});
            that.close();
          }
        }, "login", this._model.get("uid"), this._model.get("password"));
      }
    }, this);

    this.setFocusOrder([uid, password, login]);

    if(qx.core.Environment.get("qx.debug")){
      uid.setValue(gosa.LocalConfig.user);
      password.setValue(gosa.LocalConfig.password);
      login.execute();
    }
  },

  events: {
    "login": "qx.event.type.Data"
  }
});

