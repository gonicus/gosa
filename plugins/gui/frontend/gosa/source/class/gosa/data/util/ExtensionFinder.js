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
/**
 * Helps to find/manage dependencies of extensions.
 */
qx.Class.define("gosa.data.util.ExtensionFinder", {

  extend : qx.core.Object,

  /**
   * @param object {gosa.proxy.Object} The object of which extensions shall be handled
   */
  construct : function(object) {
    this.base(arguments);
    qx.core.Assert.assertInstance(object, gosa.proxy.Object);
    this.__object = object;

    gosa.io.Sse.getInstance().addListener("ExtensionAllowed", this._onExtensionAllowed, this);
  },

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events : {
    "extensionsChanged": "qx.event.type.Event"
  },

  members : {
    __object : null,

    /**
     * Handles backend event that indicate if an extension is allowed or not
     * @param ev {Event}
     */
    _onExtensionAllowed: function(ev) {
      var data = ev.getData();
      var states = this.__object.extensionStates;
      if ((data.UUID && this.__object.uuid === data.UUID) || (data.DN && data.DN === this.__object.dn)) {
        var valid = data.Allowed.toLowerCase() === "true";
        if (states[data.ExtensionName].allowed !== valid) {
          states[data.ExtensionName].allowed = valid;
          this.fireEvent("extensionsChanged");
        }
      }
    },

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
        if (!value && this.__object.extensionStates[extName].allowed === true) {
          result.push(extName);
        }
      }, this);
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
     * Finds all extensions that are dependent the stated one and that are currently in the object.
     *
     * @param extension {String} Name of the extension to find dependencies for
     * @return {Array} List of extension names (might be empty)
     */
    getExistingDependencies : function(extension) {
      return this.__getAllExtensionsDependentOn(extension).filter(this.isActiveExtension, this);
    },

    /**
     * Checks if the given extension is currently attached to the object.
     *
     * @param extension {String} Name of the extension
     * @return {Boolean} If the extension is attached
     */
    isActiveExtension : function(extension) {
      return !!this.__object.extensionTypes[extension];
    },

    /**
     * Finds all extensions that are dependent on the stated extension.
     *
     * @param extension {String} Name of the extension
     * @return {Array} Unique list of extension names, might be empty
     */
    __getAllExtensionsDependentOn : function(extension) {
      var result = [];
      gosa.util.Object.iterate(this.__object.extensionDeps, function(extName, value) {
        if (qx.lang.Array.contains(value, extension) && !qx.lang.Array.contains(result, extName)) {
          result.push(extName);
        }
      });
      return result;
    },

    /**
     * Finds all extensions that should be in the object, but are not.
     *
     * @param extension {String} Name of the extension to find dependencies for
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
    gosa.io.Sse.getInstance().removeListener("ExtensionAllowed", this._onExtensionAllowed, this);
    this.__object = null;
  }
});