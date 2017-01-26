/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Dialog for editing dashboard widgets
 */
qx.Class.define("gosa.ui.dialogs.EditDashboardWidget", {
  extend: gosa.ui.dialogs.Dialog,

  construct: function(widget) {
    this.base(arguments, this.tr("Edit dashboard widget"));

    this.__selectionValues = {};
    this.__initialValues = {};

    // form
    var form = this.__form = new qx.ui.form.Form();
    // add the form items
    this.addFormItem(new qx.ui.form.TextField(widget.getBackgroundColor()), this.tr("Background color"), null, "backgroundColor");

    var options = gosa.data.DashboardController.getWidgetOptions(widget);
    if (options.settings) {
      Object.getOwnPropertyNames(options.settings.properties).forEach(function(propertyName) {
        var typeSettings = options.settings.properties[propertyName];
        var type, title = propertyName;
        
        if (qx.lang.Type.isObject(typeSettings)) {
          type = typeSettings.type;
          if (typeSettings.title) {
            title = typeSettings.title;
            if (title.translate) {
              // trigger the translation
              title = title.translate();
            }
          }
        } else {
          type = typeSettings;
        }
        var formItem, value = widget.get(propertyName);
        this.__initialValues[propertyName] = value === null ? "" : value;
        switch (type) {
          case "Json":
            formItem = new qx.ui.form.TextArea(qx.lang.Json.stringify(value));
            break;
          case "String":
            formItem = new qx.ui.form.TextArea(value);
            break;
          case "Number":
            formItem = new qx.ui.form.Spinner(value);
            break;
          case "selection":
            var selectBox = new qx.ui.form.SelectBox();
            if (!options.settings.mandatory || options.settings.mandatory.indexOf(propertyName) === -1) {
              selectBox.add(new qx.ui.form.ListItem("-"));
            }

            if (typeSettings.provider === "RPC" && typeSettings.method) {
              // retrieve data from rpc
              gosa.io.Rpc.getInstance().cA(typeSettings.method).then(function(result) {
                for (var key in result) {
                  if (result.hasOwnProperty(key)) {
                    var item = new qx.ui.form.ListItem(result[key][typeSettings.value]);
                    var keyValue = typeSettings.key === "KEY" ? key : result[key][typeSettings.key];
                    item.setUserData("key", keyValue);
                    if (typeSettings.icon) {
                      item.setIcon(result[key][typeSettings.icon])
                    }
                    selectBox.add(item);
                    if (keyValue === value) {
                      selectBox.setSelection([item]);
                    }
                  }
                }
              }, this);
            }
            selectBox.addListener("changeSelection", function() {
              if (selectBox.getSelection().length) {
                var selectedValue = selectBox.getSelection()[0].getUserData("key");
                if (selectedValue) {
                  this.__selectionValues[propertyName] = selectedValue;
                }
              }
            }, this);
            formItem = selectBox;
            break;
        }
        if (options.settings.mandatory && options.settings.mandatory.indexOf(propertyName) >= 0) {
          formItem.setRequired(true);
        }
        this.addFormItem(formItem, title, null, propertyName);
      }, this);
    }

    // buttons
    var saveButton = gosa.ui.base.Buttons.getOkButton();
    saveButton.setAppearance("button-primary");
    saveButton.setEnabled(false);
    this.addButton(saveButton);
    var cancelButton = gosa.ui.base.Buttons.getCancelButton();
    this.addButton(cancelButton);

    // create the view
    this.addElement(new gosa.ui.form.renderer.Single(form));

    var controller = new qx.data.controller.Form(null, form);
    this.__model = controller.createModel();
    this.bind("modified", saveButton, "enabled");

    // serialization and reset /////////
    saveButton.addListener("execute", function() {
      if (form.validate()) {
        if (this.isModified()) {
          Object.getOwnPropertyNames(this.__initialValues).forEach(function(prop) {
            var value = this.__selectionValues[prop] || this.__model.get(prop);
            widget.set(prop, value);
          }, this);
          this.fireEvent("modified");
        }
        this.close();
      }
    }, this);
    cancelButton.addListener("execute", function() {
      if (this.isModified()) {
        var dialog = new gosa.ui.dialogs.Confirmation(this.tr("Unsaved changes"), this.tr("Do you want to discard those changes?"), "warning");
        dialog.addListenerOnce("confirmed", function(ev) {
          if (ev.getData() === true) {
            form.reset();
            this.close();
          }
        }, this);
        dialog.open();
      } else {
        form.reset();
        this.close();
      }
    }, this);

  },

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events : {
    "modified": "qx.event.type.Event"
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    modified: {
      check: "Boolean",
      init: false,
      event: "changeModified"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __initialValues: null,
    __selectionValues: null,
    __model: null,
    __form: null,
    
    addFormItem: function(item, label, validator, name) {
      item.setUserData("property", name);
      this.__form.add(item, label, validator, name);
      if (item instanceof qx.ui.form.SelectBox) {
        item.addListener("changeSelection", this.checkModification, this);
      } else {
        item.setLiveUpdate(true);
        item.addListener("changeValue", this.checkModification, this);
      }
    },

    /**
     * Check form for modifications
     * @return {Boolean} true if something has been modified
     */
    checkModification: function(ev) {
      var item = ev.getTarget();
      var prop = item.getUserData("property");
      var value = null;
      if (item instanceof qx.ui.form.SelectBox) {
        if (item.getSelection().length) {
          value = item.getSelection()[0].getUserData("key");
        }
      } else {
        value = item.getValue();
      }
      this.setModified(value != this.__initialValues[prop]);
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this._disposeObjects("__initialValues", "__selectionValues", "__model", "__form");
  }

});
