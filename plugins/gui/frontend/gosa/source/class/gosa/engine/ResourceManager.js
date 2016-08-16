qx.Class.define("gosa.engine.ResourceManager", {
  extend : qx.core.Object,

  construct : function() {
    this.base(arguments);
    this._registry = {};
  },

  members : {
    _registry : null,

    /**
     * @param key {String} The key for the requested resource
     * @return {String | null} The value of the resource or null, if not registered
     */
    getResource : function(key) {
      if (this._registry.hasOwnProperty(key)) {
        return this._registry[key];
      }
      return null;
    },

    /**
     * Adds a resource to the registry.
     *
     * @param key {String} The key under which the resource shall be saved
     * @param resource {String} The resource that shall be evaluated and saved
     */
    addResource : function(key, resource) {
      qx.core.Assert.assertString(key);
      qx.core.Assert.assertString(resource);

      if (this._registry.hasOwnProperty(key)) {
        this.error("There is already a resource registered for the key '" + key + "'.");
        return;
      }
      this._registry[key] = this._convertResource(resource);
    },

    /**
     * @param resource {String} Resource to convert
     * @return {String} converted Resource
     */
    _convertResource : function(resource) {
      qx.core.Assert.assertString(resource);
      return "/static/resources/" + resource;
    }
  },

  destruct : function() {
    this._registry = null;
  }
});
