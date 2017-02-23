/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

/**
 * Dialog for regiresting new webhooks
 */
qx.Class.define("gosa.ui.dialogs.RegisterWebhook", {
  extend: gosa.ui.dialogs.Dialog,

  construct: function(widget) {
    this.base(arguments, this.tr("Register webhook"));

    // form
    var form = this.__form = new qx.ui.form.Form();
    var mimeTypeField = new qx.ui.form.SelectBox().set({
      width: 250
    });
    gosa.io.Rpc.getInstance().cA("getAvailableMimeTypes").then(function(result) {
      Object.getOwnPropertyNames(result).forEach(function(mimeType) {
        var item = new qx.ui.form.ListItem(result[mimeType]);
        item.setUserData("mimeType", mimeType);
        mimeTypeField.add(item);
      }, this);
    }, this);

    var nameField = new qx.ui.form.TextField();
    nameField.setValid(false);
    nameField.setRequired(true);
    nameField.setInvalidMessage(this.tr("Please enter a string containing ASCII letters and optional hyphens"));
    nameField.setLiveUpdate(true);
    nameField.addListener("changeValue", function(ev) {
      var valid = !!ev.getData().match(/^[a-zA-Z-]+$/);
      nameField.setValid(valid);
      saveButton.setEnabled(valid && ev.getData().length > 0);
    }, this);
    nameField.addListenerOnce("appear", function(){
      nameField.focus();
    });

    form.add(nameField, this.tr("Sender name"), null, "name");
    form.add(mimeTypeField, this.tr("Type"), null, "type");

    // create the view
    this.addElement(new gosa.ui.form.renderer.Single(form));

    // buttons
    var saveButton = gosa.ui.base.Buttons.getOkButton();
    saveButton.setAppearance("button-primary");
    saveButton.setEnabled(false);
    this.addButton(saveButton);
    var cancelButton = gosa.ui.base.Buttons.getCancelButton();
    this.addButton(cancelButton);

    // serialization and reset /////////
    saveButton.addListener("execute", function() {
      if (form.validate()) {
        gosa.io.Rpc.getInstance().cA("registerWebhook", nameField.getValue(), mimeTypeField.getSelection()[0].getUserData("mimeType"))
        .then(function(result) {
          this.fireDataEvent("registered", result);
          this.close();
        }, this)
        .catch(function(error) {
          this.error(error);
        }, this);
      }
    }, this);
    cancelButton.addListener("execute", function() {
      form.reset();
      this.close();
    }, this);

  },

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events : {
    "registered": "qx.event.type.Data"
  }
});
