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
    form.add(this.getChildControl("name-field"), this.tr("Sender name"), null, "name");
    form.add(this.getChildControl("mime-type"), this.tr("Type"), null, "type");

    // create the view
    this.addElement(new gosa.ui.form.renderer.Single(form));

    this._createChildControl("save-button");
    this._createChildControl("cancel-button");
  },

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events : {
    "registered": "qx.event.type.Data"
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    appearance: {
      refine: true,
      init: "gosa-dialog-register-webhook"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __form: null,

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "name-field":
          control = new qx.ui.form.TextField();
          control.setValid(false);
          control.setRequired(true);
          control.setInvalidMessage(this.tr("Please enter a string containing ASCII letters and optional hyphens"));
          control.setLiveUpdate(true);
          control.addListener("changeValue", function(ev) {
            var data = ev.getData() || "";
            var valid = !!data.match(/^[a-zA-Z\-]+$/);
            control.setValid(valid);
            this.getChildControl("save-button").setEnabled(valid && data.length > 0);
          }, this);
          control.addListenerOnce("appear", function(){
            control.focus();
          });
          break;

        case "mime-type":
          control = new qx.ui.form.SelectBox().set({
            width: 250
          });
          gosa.io.Rpc.getInstance().cA("getAvailableMimeTypes").then(function(result) {
            Object.getOwnPropertyNames(result).forEach(function(mimeType) {
              var item = new qx.ui.form.ListItem(result[mimeType]);
              item.setUserData("mimeType", mimeType);
              control.add(item);
            }, this);
          }, this);
          break;

        case "error-message":
          control = new qx.ui.basic.Label();
          control.set({
            rich: true,
            wrap: true
          });
          control.addState("error");
          control.exclude();
          this.addElement(control);
          break;

        case "save-button":
          control = gosa.ui.base.Buttons.getOkButton();
          control.setEnabled(false);
          this.addButton(control);

          // serialization and reset /////////
          control.addListener("execute", function() {
            if (this.__form.validate()) {
              gosa.io.Rpc.getInstance().cA("registerWebhook", this.getChildControl("name-field").getValue(),
                this.getChildControl("mime-type").getSelection()[0].getUserData("mimeType"))
              .then(function(result) {
                this.fireDataEvent("registered", result);
                this.close();
              }, this)
              .catch(function(error) {
                this.error(error);
                var errorControl = this.getChildControl("error-message");
                errorControl.setValue(gosa.ui.dialogs.Error.getMessage(error));
                errorControl.show();
              }, this);
            }
          }, this);
          break;

        case "cancel-button":
          control = gosa.ui.base.Buttons.getCancelButton();
          this.addButton(control);
          control.addListener("execute", function() {
            this.__form.reset();
            this.close();
          }, this);
          break;
      }

      return control || this.base(arguments, id);
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this._disposeObjects("__form");
  }
});
