qx.Class.define("gosa.engine.processors.Base", {
  extend : qx.core.Object,

  properties : {
    target : {
      check : function(value) {
        return qx.Class.hasMixin(qx.Class.getByName(value.classname), qx.ui.core.MChildrenHandling);
      },
      init : null
    }
  },

  members : {
    _targetWidget : null,

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
  }
});
