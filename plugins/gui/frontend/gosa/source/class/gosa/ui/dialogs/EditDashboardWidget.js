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
    var props = widget.getLayoutProperties();

    // add the form items
    var spinner = new qx.ui.form.Spinner(1, props.colSpan, 6);
    form.add(spinner, this.tr("Colspan"), null, "colSpan");
    form.add(new qx.ui.form.TextField(widget.getBackgroundColor()), this.tr("Background color"), null, "backgroundColor");

    var properties = [];

    var options = gosa.view.Dashboard.getWidgetOptions(widget);
    if (options.settings) {
      Object.getOwnPropertyNames(options.settings.types).forEach(function(propertyName) {
        var type = options.settings.types[propertyName];
        properties.push(propertyName);
        switch (type) {
          case "Json":
            form.add(new qx.ui.form.TextArea(qx.lang.Json.stringify(widget.get(propertyName))), propertyName, null, propertyName);
            break;
          case "String":
            form.add(new qx.ui.form.TextArea(widget.get(propertyName)), propertyName, null, propertyName);
            break;
          case "Number":
            form.add(new qx.ui.form.Spinner(widget.get(propertyName)), propertyName, null, propertyName);
            break;
        }
      }, this);
    }

    // buttons
    var saveButton = gosa.ui.base.Buttons.getOkButton();
    this.addButton(saveButton);
    var cancelButton = gosa.ui.base.Buttons.getCancelButton();
    this.addButton(cancelButton);

    // create the view
    this.addElement(new qx.ui.form.renderer.Single(form));

    var controller = new qx.data.controller.Form(null, form);
    var model = controller.createModel();

    // serialization and reset /////////
    saveButton.addListener("execute", function() {
      if (form.validate()) {
        props.colSpan = model.getColSpan();
        widget.setLayoutProperties(props);
        widget.setBackgroundColor(model.getBackgroundColor());
        properties.forEach(function(prop) {
          console.log(prop+": "+model.get(prop));
          widget.set(prop, model.get(prop));
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
