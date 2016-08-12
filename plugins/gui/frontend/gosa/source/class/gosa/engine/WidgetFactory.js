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
      var addTemplates = function(jsonTemplate) {
        templates.push(gosa.util.Template.compileTemplate(jsonTemplate));
      };
      gosa.util.Template.getTemplates(obj.baseType).forEach(addTemplates);

      // extensions
      var extensions = obj.extensionTypes;
      for (var ext in extensions) {
        if (extensions.hasOwnProperty(ext)) {
          gosa.util.Template.getTemplates(ext).forEach(addTemplates);
        }
      }

      // generate widget
      var widget = new gosa.ui.widgets.ObjectEdit(obj, templates);

      // invoke callback
      if (context) {
        callback = qx.lang.Function.bind(callback, context);
      }
      callback(widget);
    }
  }
});
