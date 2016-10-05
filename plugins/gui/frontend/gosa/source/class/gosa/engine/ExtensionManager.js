qx.Class.define("gosa.engine.ExtensionManager", {
  extend : qx.core.Object,

  type : "singleton",

  construct : function() {
    this._registry = {};
  },

  members : {
    _registry : null,

    /**
     * Dispatch the given extension configuration.
     *
     * @param name {String} Name of the extension that shall do something
     * @param data {var} Configuration for the extension
     * @param target {qx.core.Object} The object for which the configuration was given
     * @param context {gosa.engine.Context} The context object in which the extension runs
     */
    handleExtension : function(name, data, target, context) {
      qx.core.Assert.assertString(name);
      qx.core.Assert.assertQxObject(target);
      qx.core.Assert.assertKeyInMap(name, this._registry, "No extension registered for '" + name + "'");

      var handler = new this._registry[name]();
      handler.process(data, target, context);
      handler.dispose();
    },

    /**
     * Registers an extension.
     *
     * @param name {String} The name of the extension (by which it can be referenced)
     * @param clazz {var} The class to register
     */
    registerExtension : function(name, clazz) {
      qx.core.Assert.assertString(name);
      qx.core.Assert.assertFunction(clazz);
      qx.core.Assert.assert(!this._registry.hasOwnProperty(name), "There is already an extension registered for '" + name + "'");
      this._registry[name] = clazz;
    }
  },

  destruct : function() {
    this._registry = null;
  }
});
