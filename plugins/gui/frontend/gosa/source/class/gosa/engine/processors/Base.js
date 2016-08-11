qx.Class.define("gosa.engine.processors.Base", {
  extend : qx.core.Object,

  /**
   * @param context {gosa.engine.Context}
   */
  construct : function(context){
    this.base(arguments);
    this._context = context;
  },

  members : {
    _context : null,

    /**
     * Processes the template and generates widget, widget registry entries, extensions, etc.
     *
     * @param node {Object} The top node of the template
     * @param target {qx.ui.core.Widget ? null} Widget where the template widget shall be added; defaults to the root
     *   widget of the context
     */
    process : function(node, target) {
      throw new Error("Processing is not implemented");
    },

    _getValue : function(node, property) {
      if (node.hasOwnProperty(property)) {
        return node[property];
      }
      return null;
    },

    _resolveSymbol : function(symbol) {
      qx.core.Assert.assertMatch(symbol, /^\s*@\w+\s*$/);
      symbol = symbol.trim().substring(1);
      return gosa.engine.SymbolTable.getInstance().resolveSymbol(symbol);
    },

    /**
     * Looks through the property values and transforms them, if necessary (e.g. makes a font object out of "font: [32, 'Arial']").
     *
     * @param properties {Map} Hash map property -> value
     * @return {Map} Properties with (maybe) transformed values
     */
    _transformProperties : function(properties) {
      qx.core.Assert.assertMap(properties);
      var value;
      for (var property in properties) {
        if (properties.hasOwnProperty(property)) {
          switch (property) {
            case "font":
              value = properties[property];
              properties[property] = new qx.bom.Font(value[0], value[1]);
              break;
          }
        }
      }
      return properties;
    },

    _handleExtensions : function(node, target) {
      var extensions = this._getValue(node, "extensions");
      if (extensions) {
        for (var extensionKey in extensions) {
          if (extensions.hasOwnProperty(extensionKey)) {
            gosa.engine.ExtensionManager.getInstance().handleExtension(extensionKey, extensions[extensionKey], target);
          }
        }
      }
    }
  },

  destruct : function()  {
    this._context = null;
  }
});
