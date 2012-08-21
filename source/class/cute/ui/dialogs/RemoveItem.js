/*
#asset(cute/*)
*/
qx.Class.define("cute.ui.dialogs.RemoveItem", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(dn)
  {
    this.base(arguments, this.tr("Remove item"), cute.Config.getImagePath("status/dialog-error.png", 48));
    this.setLayout(new qx.ui.layout.Grid(5,5));
    this.setModal(true);

    var type = "User";
    var text = qx.lang.String.format(this.tr("Do you really want to remove this '%1'? All references to other objects will be deleted too!"), [type]);
    var message = new qx.ui.basic.Label(text).set({allowShrinkX: false});
    this.add(message, {row: 1, column: 1});

    var ok = new qx.ui.form.Button(this.tr("OK"), cute.Config.getImagePath("actions/dialog-ok.png", 22));
    this.add(ok, {row: 2, column: 2});
    var cancel = new qx.ui.form.Button(this.tr("Cancel"), cute.Config.getImagePath("actions/dialog-cancel.png", 22));
    this.add(cancel, {row: 2, column: 3});
    ok.addListener("click", function(){
        this.fireEvent("remove");
        this.close();
      }, this);
    cancel.addListener("click", this.close, this);
  }, 

  events: {
    "remove": "qx.event.type.Event"
  }

});
