qx.Class.define("gosa.engine.WidgetFactory", {
  type : "static",

  statics : {

    /**
     * Create a new widget for the given object and invoke the callback afterwards.
     *
     * @param callback {Function} Called after the widget is created; only argument is the widget
     * @param context {Object ? null} Context for the callback function
     * @param obj {gosa.proxy.Object} The objects.* object for which the widget shall be created
     */
    createWidget : function(callback, context, obj) {
      qx.core.Assert.assertFunction(callback);
      qx.core.Assert.assertInstance(obj, gosa.proxy.Object);

      // collect templates
      var templates = [];
      var addTemplates = function(name) {
        qx.lang.Array.append(templates, gosa.util.Template.getTemplateObjects(name, obj.baseType));
      };

      addTemplates(obj.baseType);

      // extensions
      var extensions = obj.extensionTypes;
      for (var ext in extensions) {
        if (extensions.hasOwnProperty(ext) && extensions[ext]) {
          addTemplates(ext);
        }
      }

      // generate widget
      var widget = new gosa.ui.widgets.ObjectEdit(templates);

      // invoke callback
      if (context) {
        callback = qx.lang.Function.bind(callback, context);
      }
      callback(widget);
    },

    /**
     * Tries to find and create the dialog from the given name. It is first searched for a corresponding class under
     * {@link gosa.ui.dialogs}. If that is not found, it looks into the transferred cache of dialog templates.
     *
     * @param name {String} Name of the dialog class/template
     * @param controller {gosa.data.ObjectEditController ? null} Optional object controller
     * @return {gosa.ui.dialogs.Dialog | null} The (unopened) dialog widget
     */
    createDialog : function(name, controller) {
      qx.core.Assert.assertString(name);
      if (controller) {
        qx.core.Assert.assertInstance(controller, gosa.data.ObjectEditController);
      }

      var clazzName = name.substring(0, 1).toUpperCase() + name.substring(1);
      var clazz = qx.Class.getByName("gosa.ui.dialogs." + clazzName);

      // directly known class
      if (clazz) {
        var dialog = new clazz();
        dialog.setAutoDispose(true);
        return dialog;
      }

      // find dialog template
      var template = gosa.data.TemplateRegistry.getInstance().getDialogTemplate(name);
      if (template) {
        return new gosa.ui.dialogs.TemplateDialog(template, controller);
      }
      return null;
    }
  }
});
