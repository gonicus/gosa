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

    // form
    var form = new qx.ui.form.Form();

    // add the form items
    form.add(new qx.ui.form.TextField(widget.getBackgroundColor()), this.tr("Background color"), null, "backgroundColor");

    var properties = [];
    var selectionValues = {};

    var options = gosa.data.DashboardController.getWidgetOptions(widget);
    if (options.settings) {
      Object.getOwnPropertyNames(options.settings.properties).forEach(function(propertyName) {
        var typeSettings = options.settings.properties[propertyName];
        var type, title = propertyName;
        properties.push(propertyName);
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
        var formItem;
        switch (type) {
          case "Json":
            formItem = new qx.ui.form.TextArea(qx.lang.Json.stringify(widget.get(propertyName)));
            break;
          case "String":
            formItem = new qx.ui.form.TextArea(widget.get(propertyName));
            break;
          case "Number":
            formItem = new qx.ui.form.Spinner(widget.get(propertyName));
            break;
          case "selection":
            var selectBox = new qx.ui.form.SelectBox();
            if (!options.settings.mandatory || options.settings.mandatory.indexOf(propertyName) === -1) {
              selectBox.add(new qx.ui.form.ListItem("-"));
            }
            var currentValue = widget.get(propertyName);

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
                    if (keyValue === currentValue) {
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
                  selectionValues[propertyName] = selectedValue;
                }
              }
            }, this);
            formItem = selectBox;
            break;
        }
        if (options.settings.mandatory && options.settings.mandatory.indexOf(propertyName) >= 0) {
          formItem.setRequired(true);
        }
        form.add(formItem, title, null, propertyName);
      }, this);
    }

    // buttons
    var saveButton = gosa.ui.base.Buttons.getOkButton();
    saveButton.setAppearance("button-primary");
    this.addButton(saveButton);
    var cancelButton = gosa.ui.base.Buttons.getCancelButton();
    this.addButton(cancelButton);

    // create the view
    this.addElement(new gosa.ui.form.renderer.Single(form));

    var controller = new qx.data.controller.Form(null, form);
    var model = controller.createModel();

    // serialization and reset /////////
    saveButton.addListener("execute", function() {
      if (form.validate()) {
        widget.setBackgroundColor(model.getBackgroundColor()||null);
        properties.forEach(function(prop) {
          var value = selectionValues[prop] || model.get(prop);
          widget.set(prop, value);
        });
        this.fireEvent("modified");
        this.close();
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
    "modified": "qx.event.type.Event"
  }

});
