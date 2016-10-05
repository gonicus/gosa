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
