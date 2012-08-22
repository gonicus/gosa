/*
#asset(cute/*)
*/

qx.Class.define("cute.ui.dialogs.RpcError", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(message)
  {
    this.base(arguments, this.tr("Error"), cute.Config.getImagePath("status/dialog-error.png", 22));

    var message = new qx.ui.basic.Label(message);
    this.addElement(message);

    var retry = new qx.ui.form.Button(this.tr("Retry"), cute.Config.getImagePath("actions/dialog-retry.png", 22));
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
