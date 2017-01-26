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
    var initForm = {};

    // form
    var form = this.__form = new qx.ui.form.Form();

    // add the form items
    var options = gosa.data.DashboardController.getWidgetOptions(widget);
    if (options.settings) {
      Object.getOwnPropertyNames(options.settings.properties).forEach(function(propertyName) {
        var typeSettings = options.settings.properties[propertyName];
        var type, title = propertyName;
        var mandatory = (options.settings.mandatory && options.settings.mandatory.indexOf(propertyName) >= 0);
        
        if (qx.lang.Type.isObject(typeSettings)) {
          type = typeSettings.type.toLowerCase();
          if (typeSettings.title) {
            title = typeSettings.title;
            if (title.translate) {
              // trigger the translation
              title = title.translate();
            }
          }
        } else {
          type = typeSettings.toLowerCase();
        }
        var formItem, value = widget.get(propertyName);
        if (!value && typeSettings.defaultValue) {
          value = typeSettings.defaultValue;
        }

        var validator = null;
        switch (type) {

          case "json":
            value = qx.lang.Json.stringify(value);
            formItem = new qx.ui.form.TextArea();
            validator = this.validationWrapper("string", mandatory);
            break;

          case "number":
            formItem = new qx.ui.form.Spinner();
            validator = this.validationWrapper(type, mandatory);
            break;

          case "selection":
            var selectBox = new qx.ui.form.SelectBox();
            var selectionController = new qx.data.controller.List(null, selectBox);
            selectionController.setDelegate({
              bindItem: function(controller, item, index) {
                controller.bindProperty("label", "label", null, item, index);
                controller.bindProperty("data", "model", null, item, index);
                controller.bindProperty("icon", "icon", null, item, index);
              }
            });
            var data = new qx.data.Array();

            if (!typeSettings.defaultValue && (!options.settings.mandatory || options.settings.mandatory.indexOf(propertyName) === -1)) {
              data.push({label: "-", data: null});
            }

            if (typeSettings.provider === "RPC" && typeSettings.method) {
              // retrieve data from rpc
              gosa.io.Rpc.getInstance().cA(typeSettings.method).then(function(result) {

                for (var key in result) {
                  if (result.hasOwnProperty(key)) {
                    var keyValue = typeSettings.key === "KEY" ? key : result[key][typeSettings.key];
                    var entry = { data: keyValue, label: result[key][typeSettings.value]};
                    if (typeSettings.icon) {
                      entry.icon = result[key][typeSettings.icon]
                    }
                    data.push(entry);
                  }
                }
              }, this);
            } else if (typeSettings.provider === "custom" && typeSettings.options) {
              data.append(typeSettings.options);
            }

            var selectionModel = qx.data.marshal.Json.createModel(data.toArray());
            selectionController.setModel(selectionModel);

            selectBox.addListener("changeSelection", function() {
              if (selectBox.getModelSelection().length) {
                var selectedValue = selectBox.getModelSelection().getItem(0);
                if (selectedValue) {
                  this.__selectionValues[propertyName] = selectedValue;
                }
              }
            }, this);
            formItem = selectBox;
            break;

          default:
            // default (used for e.g. string type)
            formItem = new qx.ui.form.TextArea();
            validator = this.validationWrapper(type, mandatory);
            break;
        }
        if (mandatory) {
          formItem.setRequired(true);
        }
        this.addFormItem(formItem, title, validator, propertyName);
        this.__initialValues[propertyName] = value === null ? "" : value;
        if (value !== null) {
          initForm[propertyName] = value;
        }
      }, this);
    }

    // create the view
    this.addElement(new gosa.ui.form.renderer.Single(form));

    var controller = new qx.data.controller.Form(null, form);
    var model = this.__model = controller.createModel();

    // fill the model with initial values
    model.set(initForm);

    // buttons
    var saveButton = gosa.ui.base.Buttons.getOkButton();
    saveButton.setAppearance("button-primary");
    saveButton.setEnabled(false);
    this.addButton(saveButton);
    var cancelButton = gosa.ui.base.Buttons.getCancelButton();
    this.addButton(cancelButton);

    this.bind("savable", saveButton, "enabled");

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
      event: "changeModified",
      apply: "_checkSavability"
    },

    /**
     * Determines if this form can be save (is modified and valid)
     */
    savable: {
      check: "Boolean",
      init: false,
      event: "changeSavable"
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

    validationWrapper: function(type, mandatory, errorMessage) {
      var checkFunction = "check"+qx.lang.String.firstUp(type);
      if (qx.util.Validate[checkFunction]) {
        if (mandatory === true) {
          // use normal validator (also check empty values)
          return function(value) {
            qx.util.Validate[checkFunction](value, null, errorMessage);
          }
        } else {
          // use do not validate empty values
          return function(value) {
            if (value !== null && value !== undefined && value !== "") {
              qx.util.Validate[checkFunction](value, null, errorMessage);
            }
          }
        }
      }
      return null;
    },
    
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

    _checkSavability: function() {
      this.setSavable(this.isModified() && this.__form.validate());
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
      this._checkSavability();
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
