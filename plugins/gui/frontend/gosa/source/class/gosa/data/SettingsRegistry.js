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
 * A registry for system settings. Can be used to read and write settings and listen to updated on them
 *
 * Example:
 *
 * <pre class="javascript">
 *   var registry = gosa.data.SettingsRegistry.getInstance();
 *
 *   // set value
 *   registry.gosa.settings.index = false;
 *
 *   // add listener
 *   gosa.data.SettingsRegistry.addListener("gosa.settings.index", "change", function(value, old) {
 *     // do something
 *     ...
 *   }, this);
 *
 *   // change value -> listener gets called
 *   registry.gosa.settings.index = true;
 * </pre>
*/
qx.Class.define("gosa.data.SettingsRegistry", {
  type: "static",

  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    __instance: null,
    __handlers: {},
    __listeners: {},

    /**
     * Returns the root settings handler
     * @return {gosa.data.settings.Handler}
     */
    getInstance: function() {
      if (!this.__instance) {
        this.__instance = this.__createRegistryProxy(new gosa.data.settings.Handler(""));
      }
      return this.__instance;
    },

    __createRegistryProxy: function(proxiedObject) {
      return new Proxy(proxiedObject, {
        get: function(target, prop) {
          if (prop === "getInstance") {
            return target;
          } else if (target[prop]) {
            return target[prop];
          } else if (target.has(prop)) {
            return target.get(prop);
          } else if (target.getNamespace() === prop) {
            return undefined;
          } else {
            var newNamespace = target.getNamespace() ? target.getNamespace()+"."+prop : prop;
            var newEntry = gosa.data.SettingsRegistry.registerHandler(newNamespace, new gosa.data.settings.Handler());
            target.set(prop, newEntry);
            return newEntry;
          }
        },

        set: function(target, prop, value) {
          var oldValue = undefined;
          if (target.has(prop)) {
            oldValue = target.get(prop);
          }
          if (value !== oldValue) {
            gosa.data.SettingsRegistry.notifyListeners(target, prop, "change", value, oldValue);
          }
          return target.set(prop, value);
        }
      })
    },

    /**
     * Register a handler for a given path
     * @param path {String} path e.g. 'gosa.settings.index'
     * @param handler {gosa.data.ISettingsRegistryHandler}
     * @return {Proxy} the handler poxy object
     * @throws {Error} when there is already a handler registeres on this path
     */
    registerHandler: function(path, handler) {
      qx.core.Assert.assertInterface(handler, gosa.data.ISettingsRegistryHandler);
      var blockedBy = null;
      Object.getOwnPropertyNames(this.__handlers).some(function(registeredPath) {
        if (path === registeredPath) {
          blockedBy = registeredPath;
          return true;
        }
      }, this);
      if (blockedBy) {
        throw new Error("There is already a handler registered in path "+blockedBy);
      } else {
        this.__handlers[path] = handler;
        handler.setNamespace(path);
        return this.__createRegistryProxy(handler);
      }
    },

    /**
     * Returns the Handler for the given path
     * @param path {String} path e.g. gosa.settings.index
     * @return {gosa.data.ISettingsRegistryHandler|null}
     */
    getHandlerForPath: function(path) {
      while (!this.__handlers[path]) {
        var parts = path.split(".");
        parts.pop();
        path = parts.join(".");
      }
      if (path.length > 1) {
        return this.__handlers[path];
      } else {
        return null;
      }
    },

    /**
     * Notify the listeners about an event
     *
     * @param handler {gosa.data.ISettingsRegistryHandler} The settings handler
     * @param property {String} property name
     * @param event {String} Event type
     */
    notifyListeners: function(handler, property, event) {
      var args = Array.prototype.slice.call(arguments, 3);
      if (this.__listeners[handler.getNamespace()] &&
          this.__listeners[handler.getNamespace()][property] &&
          this.__listeners[handler.getNamespace()][property][event]) {
        this.__listeners[handler.getNamespace()][property][event].forEach(function(tuple) {
          tuple[0].apply(tuple[1], args);
        }, this)
      }
    },

    /**
     * Adds a listener for an event on the given path
     * @param path {String} path e.g. 'gosa.settings.index'
     * @param event {String} event type e.g. 'change'
     * @param callback {Function} event handler
     * @param context {Object} event handler context
     */
    addListener: function(path, event, callback, context) {
      var pathParts = path.split(".");
      var property = pathParts.pop();
      var handlerPath = pathParts.join(".");
      if (!this.__listeners[handlerPath]) {
        this.__listeners[handlerPath] = {};
      }
      if (!this.__listeners[handlerPath][property]) {
        this.__listeners[handlerPath][property] = {};
      }
      if (!this.__listeners[handlerPath][property][event]) {
        this.__listeners[handlerPath][property][event] = [];
      }
      this.__listeners[handlerPath][property][event].push([callback, context]);
    }
  }
});