qx.Class.define("gosa.engine.ProcessorFactory", {
  type : "static",

  statics : {
    getProcessor : function(jsonNode, context) {
      if (typeof jsonNode !== "object") {
        return null;
      }
      if (jsonNode.hasOwnProperty("type")) {
        switch (jsonNode.type) {
          case "widget":
            return new gosa.engine.processors.WidgetProcessor(context);
          case "form":
            return new gosa.engine.processors.FormProcessor();
        }
      }
      return null;
    }
  }
});
