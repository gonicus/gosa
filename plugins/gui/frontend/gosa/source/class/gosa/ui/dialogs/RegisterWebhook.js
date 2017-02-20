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

    this.__selectionValues = {};
    this.__initialValues = {};
    var initForm = {};

    // form
    var form = this.__form = new qx.ui.form.Form();
    var mimeTypeField = new qx.ui.form.SelectBox();
    gosa.io.Rpc.getInstance().cA("getAvailableMimeTypes").then(function(result) {
      result.forEach(function(mimeType) {
        var item = new qx.ui.form.ListItem(mimeType);
        mimeTypeField.add(item);
      }, this);
    }, this);

    form.add(mimeTypeField, this.tr("Mime-Type"), null, "mimeType");

    var nameField = new qx.ui.form.TextField();
    form.add(nameField, this.tr("Name"), null, "name");

    // create the view
    this.addElement(new gosa.ui.form.renderer.Single(form));

    var controller = new qx.data.controller.Form(null, form);
    var model = controller.createModel();

    // fill the model with initial values
    model.set(initForm);

    // buttons
    var saveButton = gosa.ui.base.Buttons.getOkButton();
    saveButton.setAppearance("button-primary");
    this.addButton(saveButton);
    var cancelButton = gosa.ui.base.Buttons.getCancelButton();
    this.addButton(cancelButton);

    // serialization and reset /////////
    saveButton.addListener("execute", function() {
      if (form.validate()) {
        gosa.io.Rpc.getInstance().cA("registerWebhook", nameField.getValue(), mimeTypeField.getSelection()[0].getLabel())
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
