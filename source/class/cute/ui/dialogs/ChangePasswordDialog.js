/*
#asset(cute/*)
*/
qx.Class.define("cute.ui.dialogs.ChangePasswordDialog", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(object)
  {
    this.base(arguments, this.tr("Change password..."), cute.Config.getImagePath("status/dialog-password.png", 22));
    this._object = object;
    
    // Show Subject/Message pane
    var form = new qx.ui.form.Form();
    this._form = form;

    var current = null;
    if(object.getPasswordMethod().getLength()){
      current = object.getPasswordMethod().toArray()[0];
    }

    var method = new qx.ui.form.SelectBox();
    var rpc = cute.io.Rpc.getInstance();
    rpc.cA(function(result, error){
        for(var item in result){
          var tempItem = new qx.ui.form.ListItem(result[item], null, result[item]);
          method.add(tempItem);

          if(current == result[item]){
            method.setSelection([tempItem]);
          }
        }
      }, this, "listPasswordMethods");

    // Add the form items
    var pwd1 = new qx.ui.form.PasswordField();
    pwd1.setRequired(true);
    pwd1.setWidth(200);

    var pwd2 = new qx.ui.form.PasswordField();
    pwd2.setRequired(true);
    pwd2.setWidth(200);

    form.add(method, this.tr("Method"), null, "method");
    form.add(pwd1, this.tr("New password"), null, "pwd1");
    form.add(pwd2, this.tr("New password (repeated)"), null, "pwd2");
    
    var la = new cute.ui.form.renderer.Single(form, false);
    la.getLayout().setColumnAlign(0, "left", "middle");
    this.addElement(la);
    var controller = new qx.data.controller.Form(null, form);

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

    var ok = cute.ui.base.Buttons.getButton(this.tr("Set password"), "status/dialog-password.png");
    ok.addState("default");
    ok.addListener("execute", this.setPassword, this);

    var cancel = cute.ui.base.Buttons.getCancelButton();
    cancel.addState("default");
    cancel.addListener("execute", this.close, this);

    this.addButton(ok);
    this.addButton(cancel);

    this.setFocusOrder([pwd1, pwd2, ok]);
  },

  members : {

    updateStatus : function()
    {
      //TODO: show strength password strength / policy

      if (this._pwd1.getValue() == this._pwd2.getValue()) {
        this._info.setValue("");
        this._info.exclude();
      } else {
        this._info.setValue("<span style='color:red'>" + this.tr("Passwords do not match!") + "</span>");
        this._info.show();
      }
    },

    setPassword : function()
    {
      if (this._form.validate()) {
        if (this._model.get("pwd1") != this._model.get("pwd2")) {
            return;
        }

        this._object.changePasswordMethod(function(response, error){
          if (error) {
            new cute.ui.dialogs.Error(error.message).open();
          } else {
            this.close();
            new cute.ui.dialogs.Info(this.tr("Password has been changed successfully.")).open();
          } 
          
        }, this, this._model.get("method"), this._model.get("pwd1"));
      }
    }

  }

});
