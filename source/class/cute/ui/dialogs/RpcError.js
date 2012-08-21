/*
#asset(cute/*)
*/

qx.Class.define("cute.ui.dialogs.RpcError", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(message)
  {
    this.base(arguments, this.tr("Error"));

    var image = new qx.ui.basic.Image(cute.Config.getImagePath("status/dialog-error.png", 48));

    var layout = new qx.ui.layout.Grid(9, 5);
    layout.setRowAlign(2, "right", "top");
    layout.setColumnFlex(1, 1);
    layout.setRowFlex(1, 1);
    this.setLayout(layout);
    
    var message = new qx.ui.basic.Label(message);
    this.add(image, {row: 1, column: 0});
    this.add(message, {row: 1, column: 1});

    var retry = new qx.ui.form.Button(this.tr("Retry")).set({allowGrowX: false}, cute.Config.getImagePath("actions/dialog-retry.png", 22));
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
