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
 * Filters a map by only allowing a certain amount of distinct values of a defined property.
 * e.g.
*/
qx.Class.define("gosa.data.filter.AllowedValues", {
  extend : qx.core.Object,

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    propertyName: {
      check: "String",
      nullable: true
    },

    /**
     * Maxmim allowed values
     */
    maximum: {
      check: "Integer",
      init : 1
    }
  },
    
  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __distinctValues: null,

    warmup: function(list) {
      var tmp = {};

      if (!this.getPropertyName()) {
        this.warn("no property name defined");
        return;
      }
      list.forEach(function(entry) {
        if (entry.hasOwnProperty(this.getPropertyName())) {
          tmp[entry[this.getPropertyName()]] = 1;
        }
      }, this);
      this.__distinctValues = Object.getOwnPropertyNames(tmp);
    },

    filter: function(list) {
      if (!this.getPropertyName()) {
        this.warn("no property name defined");
        return;
      }
      if (this.__distinctValues.length < this.getMaximum()) {
        // allowed maximum not reached yet
        return list;
      }
      return list.filter(function(entry) {
        return !entry.hasOwnProperty(this.getPropertyName()) || this.__distinctValues.indexOf(entry[this.getPropertyName()]) >= 0;
      }, this);
    }
  }
});