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
  construct : function(namespace) {
    this.base(arguments);
    this.__registry = {};
    if (namespace) {
      this.setNamespace(namespace);
    }
    this._rpc = gosa.io.Rpc.getInstance();
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
      init: true
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

    has: function(key) {
      return this.__registry.hasOwnProperty(key);
    },

    set: function(key, value) {
      if (!key) { return false; }
      this.__registry[key] = value;
      if (!(value instanceof Object && qx.Class.implementsInterface(value, gosa.data.ISettingsRegistryHandler))) {
        // send to backend
        this._rpc.cA("changeSetting", this.getNamespace() + "." + key, value);
      }
      return true;
    },

    get: function(key) {
      return this.__registry[key];
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