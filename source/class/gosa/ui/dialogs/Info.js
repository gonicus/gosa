/*
#asset(gosa/*)
*/
qx.Class.define("gosa.ui.dialogs.Info", {

  extend: gosa.ui.dialogs.Dialog,

  construct: function(msg)
  {
    this.base(arguments, this.tr("Info"), gosa.Config.getImagePath("status/dialog-information.png", 22));
    
    var message = new qx.ui.basic.Label(msg);
    this.addElement(message);

    var ok = gosa.ui.base.Buttons.getOkButton();
    ok.addListener("execute", this.close, this);
    this.addButton(ok);
  }

});
