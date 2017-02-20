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
* A handler for a path in the settings registry
*/
qx.Class.define("gosa.data.settings.Handler", {
  extend : qx.core.Object,
  implement: gosa.data.ISettingsRegistryHandler,

  /*
   *****************************************************************************
   CONSTRUCTOR
   *****************************************************************************
   */
  construct : function(namespace, config) {
    this.base(arguments);
    this.__registry = {};
    if (namespace) {
      this.setNamespace(namespace);
    }
    this._rpc = gosa.io.Rpc.getInstance();

    // initialize available configuration options
    if (config) {
      if (config.items) {
        this.setItemInfos(config.items);
      }
      if (config.config) {
        this.setConfiguration(config.config);
      }
    }
  },

  /*
   *****************************************************************************
   PROPERTIES
   *****************************************************************************
   */
  properties : {
    namespace: {
      check: "String",
      init: "",
      event: "changeNamespace"
    },
    ready: {
      check: "Boolean",
      init: false
    },

    readOnly: {
      check: "Boolean",
      init: false
    },

    /**
     * The available  configuration settings (name, type, value, etc.)
     */
    itemInfos: {
      check: "Object",
      init: null,
      apply: "_applyItemInfos"
    },

    /**
     * General config settings for this Handler (e.g. readOnly setting)
     */
    configuration: {
      check: "Object",
      init: null,
      apply: "_applyConfiguration"
    }
  },

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */
  members : {
    _items: null,
    _rpc: null,
    __registry : null,
    __skipSending: null,

    _applyConfiguration: function(value) {
      Object.getOwnPropertyNames(value).forEach(function(entry) {
        switch (entry) {
          case "read_only":
            this.setReadOnly(value[entry]);
            break;
        }
      }, this);
    },

    // property apply
    _applyItemInfos: function(value) {
      this.__skipSending = true;
      Object.getOwnPropertyNames(value).forEach(function(property) {
        this.set(property, this._convertIncomingValue(value[property]));
      }, this);
      this.setReady(true);
      this.__skipSending = false;
    },

    refreshItemInfos: function() {
      this._rpc.cA("getItemInfos", this.getNamespace()).then(this.setItemInfos, this)
    },

    has: function(key) {
      return this.__registry.hasOwnProperty(key);
    },

    set: function(key, value) {
      if (this.isReadOnly()) { return false; }
      if (!key) { return false; }
      if (this.__registry[key] !== value) {
        this.__registry[key] = value;
        // send to backend
        if (!this.__skipSending) {
          this._rpc.cA("changeSetting", this.getNamespace() + "." + key, value);
        }
        return true;
      } else {
        return false;
      }
    },

    get: function(key) {
      return this.__registry[key];
    },

    _convertIncomingValue: function(itemInfo) {
      var type = itemInfo.type || "string";
      var value = itemInfo.value;
      if (qx.lang.Type.isArray(type)) {
        if (value in type) {
          return value;
        } else {
          return null;
        }
      }
      switch (type.toLowerCase()) {
        case "boolean":
          if (qx.lang.Type.isBoolean(value)) {
            return value;
          }
          return qx.lang.Type.isString(value) ? value.toLowerCase() == "true" : !!value;
        case "number":
          return parseFloat(value);
        case "string":
        default:
          return value;
      }
    }

  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this._rpc = null;
    this._disposeObjects("__registry");
  }
});