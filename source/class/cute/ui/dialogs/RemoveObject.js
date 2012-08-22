/*
#asset(cute/*)
*/
qx.Class.define("cute.ui.dialogs.RemoveObject", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(dn)
  {
    this.base(arguments, this.tr("Remove object"), cute.Config.getImagePath("status/dialog-error.png", 22));

    this.setWidth(400);

    //var text = qx.lang.String.format(this.tr("Do you want to remove this %1 object including all of its references to other objects?"), [type]);
    var text = this.tr("Do you want to remove this object including all of its references to other objects?");
    var message = new qx.ui.basic.Label(text);
    message.setRich(true);
    message.setWrap(true);
    this.addElement(message);

    var ok = new qx.ui.form.Button(this.tr("OK"), cute.Config.getImagePath("actions/dialog-ok.png", 22));
    this.addButton(ok);

    var cancel = new qx.ui.form.Button(this.tr("Cancel"), cute.Config.getImagePath("actions/dialog-cancel.png", 22));
    this.addButton(cancel);
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
