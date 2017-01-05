/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.engine.ResourceManager", {
  extend : qx.core.Object,

  construct : function() {
    this.base(arguments);
    this._registry = {};
  },

  statics : {
   /**
     * @param resource {String} Resource to convert
     * @return {String} converted Resource
     */
    convertResource : function(resource) {
      qx.core.Assert.assertString(resource);
      if (qx.util.ResourceManager.getInstance().isFontUri(resource)) {
        return resource;
      }
      return "/static/resources/" + resource;
    }
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
      this._registry[key] = this.self(arguments).convertResource(resource);
    }
  },

  destruct : function() {
    this._registry = null;
  }
});
