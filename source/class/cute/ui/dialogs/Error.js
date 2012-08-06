qx.Class.define("cute.ui.dialogs.Error", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(message)
  {
    this.base(arguments, this.tr("An error occured"), "cute/errorDialog.png");
    this.setLayout(new qx.ui.layout.Grid(5,5));
    this.setModal(true);
    
    var message = new qx.ui.basic.Label(message);
    this.add(message, {row: 1, column: 1});

    var ok = new qx.ui.form.Button(this.tr("Ok"));
    this.add(ok, {row: 2, column: 2});;
    ok.addListener("click", this.close, this);
  }

});
