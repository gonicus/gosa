qx.Class.define("cute.ui.dialogs.RpcError", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(message)
  {
    this.base(arguments, this.tr("An error occured"), "cute/errorDialog.png");
    this.setLayout(new qx.ui.layout.Grid(5,5));
    
    var message = new qx.ui.basic.Label(message);
    this.add(message, {row: 1, column: 1});


    var retry = new qx.ui.form.Button(this.tr("Retry"));
    this.add(retry, {row: 2, column: 3});;
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
