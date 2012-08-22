/*
#asset(cute/*)
*/
qx.Class.define("cute.ui.dialogs.SendMessageDialog", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(object)
  {
    this.base(arguments, this.tr("Send message..."));
    this.setModal(true);

    this._object = object;
    
    // Show Subject/Message pane
    var form = new qx.ui.form.Form();
    this._form = form;

    // Add the form items
    var subject = new qx.ui.form.TextField();
    subject.setRequired(true);
    subject.setWidth(200);

    var message = new qx.ui.form.TextArea();
    message.setRequired(true);
    message.setWidth(400);
    message.setHeight(200);

    form.add(subject, this.tr("Subject"), null, "subject");
    form.add(message, this.tr("Message"), null, "message");
    
    this.addElement(new cute.ui.form.renderer.Single(form));
    var controller = new qx.data.controller.Form(null, form);
    this._model = controller.createModel();

    var ok = cute.ui.base.Buttons.getButton(this.tr("Send"), "actions/message-send.png");
    ok.addState("default");
    ok.addListener("execute", this.send, this);

    var cancel = cute.ui.base.Buttons.getCancelButton();
    cancel.addState("default");
    cancel.addListener("execute", this.close, this);

    this.addButton(ok);
    this.addButton(cancel);

    this.setFocusOrder([subject, message, ok]);
  },

  members : {

    send : function()
    {
      if (this._form.validate()) {

        this._object.notify(function(response, error){
          if (error) {
            new cute.ui.dialogs.Error(error.message).open();
          } else {
            this.close();
          } 
          
        }, this, this._model.get("subject"), this._model.get("message"));
      }
    }

  }

});
