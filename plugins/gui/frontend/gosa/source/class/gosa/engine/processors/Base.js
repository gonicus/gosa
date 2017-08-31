/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

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
    _firstLevelExtensionsProcessed : false,

    /**
     * Processes the template and generates widget, widget registry entries, extensions, etc.
     *
     * @param node {Object} The top node of the template
     * @param target {qx.ui.core.Widget} Widget where the template widget shall be added
     * @param attributes {Array} List of attributes/model paths (as string) for which widgets shall be created. If an
     *   attribute is not in this array, no widget is created.
     */
    process : function(node, target, attributes) {
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
     * Looks through the property values and transforms them, if necessary (e.g. makes a font object out of
     * "font: [32, 'Arial']").
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
            case "value":
              properties[property] = new qx.data.Array(properties[property]);
              break;
          }
        }
      }
      return properties;
    },


    processFirstLevelExtensions : function(node, target) {
      if (this._getValue(node, "class")) {
        this._firstLevelExtensionsProcessed = true;
        this._handleExtensions(node, target);
      }
    },

    _handleExtensions : function(node, target) {
      var extensions = this._getValue(node, "extensions");
      var extensionManager = gosa.engine.ExtensionManager.getInstance();
      if (extensions) {
        // 'resources' extension must be loaded first
        if (extensions.hasOwnProperty("resources")) {
          extensionManager.handleExtension("resources", extensions.resources, target, this._context);
        }

        // all other extensions
        for (var extensionKey in extensions) {
          if (extensionKey !== "resources" && extensions.hasOwnProperty(extensionKey)) {
            extensionManager.handleExtension(extensionKey, extensions[extensionKey], target, this._context);
          }
        }
      }
    }
  },

  destruct : function()  {
    this._context = null;
  }
});
