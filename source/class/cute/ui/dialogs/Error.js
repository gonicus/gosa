/*
#asset(cute/*)
*/
qx.Class.define("cute.ui.dialogs.Error", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(message)
  {
    this.base(arguments, this.tr("Error"), cute.Config.getImagePath("status/dialog-error.png", 22));
    
    var message = new qx.ui.basic.Label(message);
    this.addElement(message);

    var ok = new qx.ui.form.Button(this.tr("OK"), cute.Config.getImagePath("actions/dialog-ok.png", 22));
    ok.addListener("execute", this.close, this);
    this.addButton(ok);
  }

});
