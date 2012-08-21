/*
#asset(cute/*)
*/

qx.Class.define("cute.ui.dialogs.RpcError", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(message)
  {
    this.base(arguments, this.tr("Error"));

    var image = new qx.ui.basic.Image("cute/images/48/status/dialog-error.png")

    var layout = new qx.ui.layout.Grid(9, 5);
    layout.setRowAlign(2, "right", "top");
    layout.setColumnFlex(1, 1);
    layout.setRowFlex(1, 1);
    this.setLayout(layout);
    
    var message = new qx.ui.basic.Label(message);
    this.add(image, {row: 1, column: 0});
    this.add(message, {row: 1, column: 1});

    var retry = new qx.ui.form.Button(this.tr("Retry")).set({allowGrowX: false}, "cute/images/22/actions/dialog-retry.png");
    this.add(retry, {row: 2, column: 0, colSpan: 3});
    retry.addListener("click", function(){
        this.close();
        this.fireEvent("retry");
      }, this);
  },

  events: {
    "retry" : "qx.event.type.Event"
  }
});
