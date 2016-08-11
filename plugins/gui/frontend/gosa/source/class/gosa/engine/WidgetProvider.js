qx.Class.define("gosa.engine.WidgetProvider", {
  type : "static",

  statics : {

    /**
     * Create a new widget for the given object and invoke the callback afterwards.
     *
     * @param callback {Function} Called after the widget is created; only argument is the widget
     * @param context {Object ? null} Context for the callback function
     * @param obj {Object} The objects.* object for which the widget shall be created
     */
    createWidget : function(callback, context, obj) {
      qx.core.Assert.assertFunction(callback);
      qx.core.Assert.assertObject(obj);
      qx.core.Assert.assertTrue(
        qx.lang.String.startsWith(obj.classname, "objects."),
        "The object must be of the type objects.*"
      );

      // get template
      var objectName = obj.baseType;
      if (!gosa.Cache.gui_templates.hasOwnProperty(objectName)) {
        qx.log.Logger.error("No template found for '" + objectName + "'.");
        return;
      }
      var templateRaw = gosa.Cache.gui_templates[objectName][0];
      var template = JSON.parse(templateRaw);

      // generate widget
      var templateContext = new gosa.engine.Context(template);

      // invoke callback
      if (context) {
        callback = qx.lang.Function.bind(callback, context);
      }
      callback(templateContext.getRootWidget());
    }
  }
});
