/*
#asset(gosa/*)
*/
qx.Class.define("gosa.ui.dialogs.RemoveObject", {

  extend: gosa.ui.dialogs.Dialog,

  construct: function(dn)
  {
    this.base(arguments, this.tr("Remove object"), gosa.Config.getImagePath("status/dialog-error.png", 22));

    this.setWidth(400);

    //var text = qx.lang.String.format(this.tr("Do you want to remove this %1 object including all of its references to other objects?"), [type]);
    var text = this.tr("Do you want to remove this object including all of its references to other objects?");
    var message = new qx.ui.basic.Label(text);
    message.setRich(true);
    message.setWrap(true);
    this.addElement(message);

    var ok = gosa.ui.base.Buttons.getOkButton();
    this.addButton(ok);

    var cancel = gosa.ui.base.Buttons.getCancelButton();
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
