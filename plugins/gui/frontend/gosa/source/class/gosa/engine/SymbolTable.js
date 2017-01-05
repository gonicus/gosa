/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.engine.SymbolTable", {
  extend : qx.core.Object,
  type : "singleton",

  construct : function() {
    this._table = {};
  },

  members : {
    _table : null,

    addSymbol : function(symbol, value) {
      qx.core.Assert.assertString(symbol, "Symbol must be a string");
      qx.core.Assert.assert(!this._table.hasOwnProperty(symbol), "Symbol '" + symbol + "' is already defined");
      this._table[symbol] = value;
    },

    resolveSymbol : function(symbol) {
      qx.core.Assert.assertString(symbol, "Symbol must be a string");
      if (!this._table.hasOwnProperty(symbol)) {
        qx.log.Logger.warn("Symbol '" + symbol + "' is unknown");
      }
      return this._table[symbol];
    }
  },

  destruct : function() {
    this._disposeObjects("_table");
  }
});
