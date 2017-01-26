/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */
/**
 * Helps to find/manage dependencies of extensions.
 */
qx.Class.define("gosa.data.ExtensionFinder", {

  extend : qx.core.Object,

  /**
   * @param object {gosa.proxy.Object} The object of which extensions shall be handled
   */
  construct : function(object) {
    this.base(arguments);
    qx.core.Assert.assertInstance(object, gosa.proxy.Object);
    this.__object = object;
  },

  members : {
    __object : null,

    /**
     * Returns all extensions of the object in an order that prevents dependency faults.
     *
     * @return {Array} List of extension names (Strings); might be empty
     */
    getOrderedExtensions : function() {
      var result = [];
      var deps = this.__object.extensionDeps;

      var resolveDep = function(name) {
        var currentDeps = deps[name];
        if (currentDeps.length > 0) {
          for (var ext in currentDeps) {
            if (currentDeps.hasOwnProperty(ext)) {
              resolveDep(currentDeps[ext]);
            }
          }
        }
        if (!qx.lang.Array.contains(result, name)) {
          result.push(name);
        }
      };

      for (var ext in deps) {
        if (deps.hasOwnProperty(ext)) {
          resolveDep(ext);
        }
      }
      return result;
    },

    /**
     * @return {Array} Names of extensions that are currently active
     */
    getCurrentExtensions : function() {
      var result = [];
      gosa.util.Object.iterate(this.__object.extensionTypes, function(extensionName, value) {
        if (value && !qx.lang.Array.contains(result, extensionName)) {
          result.push(extensionName);
        }
      });
      return result;
    },

    /**
     * Returns a list of extensions that the object can be extended by.
     *
     * @return {Array} List of extension names (as strings); might be empty
     */
    getAddableExtensions : function() {
      var result = [];
      gosa.util.Object.iterate(this.__object.extensionTypes, function(extName, value) {
        if (!value) {
          result.push(extName);
        }
      });
      return result;
    },

    /**
     * Returns a list of extensions that can be retracted from the object.
     *
     * @return {Array} List of extension names (as strings); might be empty
     */
    getRetractableExtensions : function() {
      var result = [];
      gosa.util.Object.iterate(this.__object.extensionTypes, function(extName, value) {
        if (value) {
          result.push(extName);
        }
      });
      return result;
    },

    /**
     * Finds all extensions that should be in the object, but are not.
     *
     * @param extension {String} Nme of the extension to find dependencies for
     * @return {Array} A list of extension dependency names that are not attached to the object at the moment
     */
    getMissingDependencies : function(extension) {
      var dependencies = this.__object.extensionDeps[extension]
        ? qx.lang.Array.clone(this.__object.extensionDeps[extension])
        : [];

      dependencies = dependencies.filter(function(ext) {
        return !this.__object.extensionTypes[ext];
      }, this);
      return dependencies;
    },

    /**
     * @return {Object} Key: name of extension with missing dependencies, value: array of dependent extension names (in
     *   no particular order)
     */
    getAllMissingExtensions : function() {
      var missingExtensions = {};
      this.getCurrentExtensions().forEach(function(extName) {
        missingExtensions[extName] = this.getMissingDependencies(extName);
      }, this);
      return missingExtensions;
    },

    /**
     * @return {Array} Unique names of extensions
     */
    getAllMissingExtensionsAsArray : function() {
      return qx.lang.Array.unique([].concat.apply([], Object.values(this.getAllMissingExtensions())));
    }
  },

  destruct : function() {
    this.__object = null;
  }
});