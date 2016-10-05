qx.Class.define("gosa.engine.ProcessorFactory", {
  type : "static",

  statics : {

    /**
     * Finds the correct processor for the given jsonNode.
     *
     * @param template {Object} The (already parsed) template
     * @param context {gosa.engine.Context} The context in which the processor shall run
     */
    getProcessor : function(template, context) {
      qx.core.Assert.assertObject(template);

      if (template.hasOwnProperty("type")) {
        switch (template.type) {
          case "widget":
            return new gosa.engine.processors.WidgetProcessor(context);
          case "form":
            return new gosa.engine.processors.FormProcessor(context);
        }
      }
      return null;
    }
  }
});
