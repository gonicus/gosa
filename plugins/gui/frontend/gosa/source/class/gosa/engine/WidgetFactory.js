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
      var objectName = obj.baseType;
      if (!gosa.Cache.gui_templates.hasOwnProperty(objectName)) {
        qx.log.Logger.error("No template found for '" + objectName + "'.");
        return;
      }
      var templates = [];
      gosa.Cache.gui_templates[objectName].forEach(function(jsonTemplate) {
        templates.push(gosa.engine.TemplateCompiler.compile(jsonTemplate));
      });

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
