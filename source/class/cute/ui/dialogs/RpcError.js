/*
#asset(cute/*)
*/

qx.Class.define("cute.ui.dialogs.RpcError", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(msg)
  {
    this.base(arguments, this.tr("Error"), cute.Config.getImagePath("status/dialog-error.png", 22));

    var message = new qx.ui.basic.Label(msg);
    this.addElement(message);

    var retry = cute.ui.base.Buttons.getButton(this.tr("Retry"), "actions/dialog-retry.png");
    retry.addListener("execute", function(){
        this.close();
        this.fireEvent("retry");
    }, this);
    this.addButton(retry);
  },

  events: {
    "retry" : "qx.event.type.Event"
  }
});
