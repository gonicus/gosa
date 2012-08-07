qx.Class.define("cute.ui.dialogs.RpcError", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(message)
  {
    this.base(arguments, this.tr("An error occured"));

    var image = new qx.ui.basic.Image("cute/errorDialog.png")

    var layout = new qx.ui.layout.Grid(9, 5);
    layout.setRowAlign(2, "right", "top");
    layout.setColumnFlex(1, 1);
    layout.setRowFlex(1, 1);
    this.setLayout(layout);
    
    var message = new qx.ui.basic.Label(message);
    this.add(image, {row: 1, column: 0});
    this.add(message, {row: 1, column: 1});


    var retry = new qx.ui.form.Button(this.tr("Retry")).set({allowGrowX: false});
    this.add(retry, {row: 2, column: 0, colSpan: 3});
    retry.addListener("click", function(){
        this.close();
        this.fireEvent("retry");
      }, this);

    //var cancel = new qx.ui.form.Button(this.tr("Cancel"));
    //this.add(cancel, {row: 2, column: 2});;
    //cancel.addListener("click", function(){
    //    this.close();
    //    this.fireEvent("cancel");
    //  }, this);
  },

  events: {
    "retry" : "qx.event.type.Event",
    "cancel" : "qx.event.type.Event"
  }

});
