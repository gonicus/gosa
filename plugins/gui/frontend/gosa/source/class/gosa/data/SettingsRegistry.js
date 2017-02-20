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
 *   // register a handler for a path
 *   gosa.data.SettingsRegistry.registerHandler(new gosa.data.settings.ConfigHandler("gosa.settings"));
 *
 *   // set value
 *   gosa.data.SettingsRegistry.set("gosa.settings.index", false);
 *
 *   // add listener
 *   gosa.data.SettingsRegistry.addListener("gosa.settings.index", "change", function(value, old) {
 *     // do something
 *     ...
 *   }, this);
 *
 *   // change value -> listener gets called
 *   gosa.data.SettingsRegistry.set("gosa.settings.index", true);
 *
 *   // get value
 *   gosa.data.SettingsRegistry.get("gosa.settings.index");
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
    __editors: {},

    load: function() {
      gosa.io.Rpc.getInstance().cA("getSettingHandlers").bind(this)
      .then(function(result) {
        Object.getOwnPropertyNames(result).forEach(function(handlerPath) {
          if (!this.__handlers[handlerPath]) {
            this.registerHandler(new gosa.data.settings.Handler(handlerPath, result[handlerPath]));
          } else {
            // existing handler for this path -> update infos
            this.__handlers[handlerPath].setItemInfos(result[handlerPath]['items']);
            this.__handlers[handlerPath].setConfiguration(result[handlerPath]['config']);
          }
        }, this);
      });
    },

    refresh: function(handlerPath) {
      return gosa.io.Rpc.getInstance().cA("getItemInfos", handlerPath)
      .then(this.__handlers[handlerPath].setItemInfos, this.__handlers[handlerPath])
      .catch(gosa.ui.dialogs.Error.show);
    },

    getHandlers: function() {
      var handlers = new qx.data.Array();
      Object.getOwnPropertyNames(this.__handlers).forEach(function(path) {
        handlers.push(this.__handlers[path]);
      }, this);
      return handlers;
    },

    /**
     * Get a config setting value
     * @return {var} the current value of this setting
     */
    get: function(path) {
      var partsInfo = this.__getPathInfo(path);
      if (partsInfo.handler) {
        return partsInfo.handler.get(partsInfo.param);
      } else {
        return undefined;
      }
    },

    /**
     * Set a config setting value
     * @param path {String} path to setting
     * @param value {var} value to set
     * @return {Boolean} false if the setting does not exist
     */
    set: function(path, value) {
      var partsInfo = this.__getPathInfo(path);
      if (partsInfo.handler) {
        partsInfo.handler.set(partsInfo.param, value);
        return true;
      } else {
        return false;
      }
    },

    __getPathInfo: function(path) {
      var parts = path.split(".");
      var param = parts.pop();

      while (parts.length > 0 && !this.__handlers[parts.join(".")]) {
        param = parts.pop()+".".param;
      }
      return {
        path: parts.join("."),
        param: param,
        handler: this.__handlers[parts.join(".")]
      }
    },

    /**
     * Register a handler for a given path
     * @param handler {gosa.data.ISettingsRegistryHandler}
     * @throws {Error} when there is already a handler registered on this path
     */
    registerHandler: function(handler) {
      qx.core.Assert.assertInterface(handler, gosa.data.ISettingsRegistryHandler);
      var blockedBy = null;
      var path = handler.getNamespace();
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
      }
    },

    /**
     * Unregister a settings handler from its namespace path
     * @param handler {gosa.data.ISettingsRegistryHandler}
     */
    unregisterHandler: function(handler) {
      if (handler.getNamespace() in this.__handlers) {
        delete this.__handlers[handler.getNamespace()];
      }
    },

    /**
     * Register a editor page for a namespace
     * @param namespace {String} namespace e.g. gosa.settings
     * @param editor {qx.ui.core.Widget}
     */
    registerEditor: function(namespace, editor) {
      qx.core.Assert.assertString(namespace);
      qx.core.Assert.assertInstance(editor, qx.ui.core.Widget);
      this.__editors[namespace] = editor;
    },

    /**
     * Unregister editor for this path
     * @param namespace {String} namespace e.g. gosa.settings
     */
    unregisterEditor: function(namespace) {
      delete this.__editors[namespace];
    },

    /**
     * Returns the registers editor for this namespace
     * @param namespace {String} namespace e.g. gosa.settings
     * @return {qx.ui.core.Widget|null}
     */
    getEditor: function(namespace) {
      return this.__editors[namespace];
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