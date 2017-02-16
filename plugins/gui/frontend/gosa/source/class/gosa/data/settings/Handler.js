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
  construct : function(namespace, infos) {
    this.base(arguments);
    this.__registry = {};
    if (namespace) {
      this.setNamespace(namespace);
    }
    this._rpc = gosa.io.Rpc.getInstance();

    // initialize available configuration options
    if (!infos) {
      this._rpc.cA("getItemInfos", this.getNamespace()).then(this.setItemInfos, this)
    } else {
      this.setItemInfos(infos)
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
      init: ""
    },
    ready: {
      check: "Boolean",
      init: false
    },
    itemInfos: {
      check: "Object",
      init: null,
      apply: "_applyItemInfos"
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

    // property apply
    _applyItemInfos: function(value) {
      this.__skipSending = true;
      Object.getOwnPropertyNames(value).forEach(function(property) {
        this.set(property, this._convertIncomingValue(value[property]));
      }, this);
      this.setReady(true);
      this.__skipSending = false;
    },

    has: function(key) {
      return this.__registry.hasOwnProperty(key);
    },

    set: function(key, value) {
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