/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/*
#asset(gosa/*)
*/
qx.Class.define("gosa.ui.dialogs.SendMessageDialog", {

  extend: gosa.ui.dialogs.Dialog,

  construct: function(object)
  {
    this.base(arguments, this.tr("Send message..."));
    this._object = object;
    
    // Show Subject/Message pane
    var form = new qx.ui.form.Form();
    this._form = form;

    // Add the form items
    var subject = new qx.ui.form.TextField();
    subject.setRequired(true);
    subject.setWidth(200);
    subject.addListener("keyup", this.updateState, this);
    this._subject = subject;

    var message = new qx.ui.form.TextArea();
    message.setRequired(true);
    message.setWidth(400);
    message.setHeight(200);
    message.addListener("keyup", this.updateState, this);
    message.setValue("");
    this._message = message;

    form.add(subject, this.tr("Subject"), null, "subject");
    form.add(message, this.tr("Message"), null, "message");
    
    var la = new gosa.ui.form.renderer.Single(form);
    la.getLayout().setColumnAlign(0, "left", "top");
    this.addElement(la);
    var controller = new qx.data.controller.Form(null, form);
    this._model = controller.createModel();

    var ok = gosa.ui.base.Buttons.getButton(this.tr("Send"), "actions/message-send.png");
    ok.addState("default");
    ok.addListener("execute", this.send, this);
    ok.setEnabled(false);
    this._ok = ok;

    var cancel = gosa.ui.base.Buttons.getCancelButton();
    cancel.addState("default");
    cancel.addListener("execute", this.close, this);

    this.addButton(ok);
    this.addButton(cancel);

    this.setFocusOrder([subject, message, ok]);
  },

  members : {

    updateState : function()
    {
      this._ok.setEnabled((this._message.getValue() != "") && (this._subject.getValue() != ""));
    },

    send : function()
    {
      if (this._form.validate()) {

        this._object.notify(function(response, error){
          if (error) {
            new gosa.ui.dialogs.Error(error.message).open();
          } else {
            this.close();
          } 
          
        }, this, this._model.get("subject"), this._model.get("message"));
      }
    }

  }

});
