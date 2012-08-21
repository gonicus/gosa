/*
#asset(cute/*)
*/
qx.Class.define("cute.ui.dialogs.Error", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(message)
  {
    this.base(arguments, this.tr("Error"), cute.Config.getImagePath("status/dialog-error.png", 22));
    this.setLayout(new qx.ui.layout.Grid(5,5));
    this.setModal(true);
    
    var message = new qx.ui.basic.Label(message);
    this.add(message, {row: 1, column: 1});

    var ok = new qx.ui.form.Button(this.tr("OK"), cute.Config.getImagePath("actions/dialog-ok.png", 22));
    this.add(ok, {row: 2, column: 2});;
    ok.addListener("click", this.close, this);
  }

});
