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

    // Add the form items
    var pwd1 = new qx.ui.form.PasswordField();
    pwd1.setRequired(true);
    pwd1.setWidth(200);

    var pwd2 = new qx.ui.form.PasswordField();
    pwd2.setRequired(true);
    pwd2.setWidth(200);

    form.add(pwd1, this.tr("New password"), null, "pwd1");
    form.add(pwd2, this.tr("New password (repeated)"), null, "pwd2");
    
    this.addElement(new cute.ui.form.renderer.Single(form));
    var controller = new qx.data.controller.Form(null, form);
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

    setPassword : function()
    {
      if (this._form.validate()) {
        alert("dingdong");
      //  this._object.notify(function(response, error){
      //    if (error) {
      //      new cute.ui.dialogs.Error(error.message).open();
      //    } else {
      //      this.close();
      //    } 
      //    
      //  }, this, this._model.get("pwd1"), this._model.get("pwd2"));
      }
    }

  }

});
