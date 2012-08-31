/*
#asset(cute/*)
*/
qx.Class.define("cute.ui.dialogs.Info", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(msg)
  {
    this.base(arguments, this.tr("Info"), cute.Config.getImagePath("status/dialog-information.png", 22));
    
    var message = new qx.ui.basic.Label(msg);
    this.addElement(message);

    var ok = cute.ui.base.Buttons.getOkButton();
    ok.addListener("execute", this.close, this);
    this.addButton(ok);
  }

});
