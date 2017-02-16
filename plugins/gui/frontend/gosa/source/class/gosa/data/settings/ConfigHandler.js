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
* A handler for accessing and changing settings the the gosa config files
*/
qx.Class.define("gosa.data.settings.ConfigHandler", {
  extend : gosa.data.settings.Handler,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function(namespace) {
    this.base(arguments, namespace);

    // initialize available configuration options
    this._rpc.cA("getItemInfos", this.getNamespace())
    .then(function(items) {
      this._items = items;
      Object.getOwnPropertyNames(items).forEach(function(property) {
        this.set(property, this._convertIncomingValue(items[property]));
      }, this);
      this.setReady(true);
    }, this)
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    ready: {
      refine: true,
      init: false
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
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
          return value.toLowerCase() == "true";
        case "number":
          return parseFloat(value);
        case "string":
        default:
          return value;
      }
    }
  }
});