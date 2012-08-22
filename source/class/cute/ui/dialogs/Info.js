/*
#asset(cute/*)
*/
qx.Class.define("cute.ui.dialogs.Info", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(message)
  {
    this.base(arguments, this.tr("Info"), cute.Config.getImagePath("status/dialog-information.png", 22));
    
    var message = new qx.ui.basic.Label(message);
    this.addElement(message);

    var ok = cute.ui.base.Buttons.getOkButton();
    ok.addListener("execute", this.close, this);
    this.addButton(ok);
  }

});
