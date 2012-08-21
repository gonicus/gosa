/*
#asset(cute/*)
*/
qx.Class.define("cute.ui.dialogs.SendMessageDialog", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(object)
  {
    this.base(arguments, this.tr("Send message..."));
    this.setLayout(new qx.ui.layout.VBox(5));
    this.setModal(true);

    this._object = object;
    
    // Show Subject/Message pane
    var form = new qx.ui.form.Form();
    this._form = form;

    // add the form items
    var subject = new qx.ui.form.TextField();
    subject.setRequired(true);
    subject.setWidth(200);

    var message = new qx.ui.form.TextArea();
    message.setRequired(true);
    message.setWidth(400);
    message.setHeight(200);

    form.add(subject, this.tr("Subject"), null, "subject");
    form.add(message, this.tr("Message"), null, "message");
    
    this.add(new cute.ui.form.renderer.Single(form));
    var controller = new qx.data.controller.Form(null, form);
    this._model = controller.createModel();

    // Add button static button line for the moment
    var paneLayout = new qx.ui.layout.HBox().set({
      spacing: 4,
      alignX : "right"
    });
    var buttonPane = new qx.ui.container.Composite(paneLayout).set({
      paddingTop: 11
    });

    var ok = new qx.ui.form.Button(this.tr("Send"), cute.Config.getImagePath("actions/message-send.png", 22));
    ok.addState("default");
    ok.addListener("execute", this.send, this);

    var cancel = new qx.ui.form.Button(this.tr("Cancel"), cute.Config.getImagePath("actions/dialog-cancel.png", 22));
    cancel.addState("default");
    cancel.addListener("execute", this.close, this);

    buttonPane.add(ok);
    buttonPane.add(cancel);
    this.add(buttonPane);
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
