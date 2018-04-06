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

    delegateFilterPropertyName: {
      check: 'String',
      nullable: true
    },

    /**
     * Maximum allowed values
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
        // only use the resolved ones
        if (entry.hasOwnProperty(this.getPropertyName()) &&
          (this.getPropertyName() !== '__identifier') || entry[this.getPropertyName()] !== entry['__identifier__']) {
          tmp[entry[this.getPropertyName()]] = 1;
        }
      }, this);
      this.__distinctValues = Object.getOwnPropertyNames(tmp);
    },

    /**
     * Return additional search options for the backend search
     * @returns {Map}
     */
    getSearchOptions: function() {
      var res = {};
      res[this.getPropertyName()] = {
        values: this.__distinctValues,
        limit: this.__distinctValues.length >= this.getMaximum()
      };
      return res;
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
    },

    delegateFilter: function(modelItem) {
      if (this.getDelegateFilterPropertyName()) {
        if (this.__distinctValues.length < this.getMaximum()) {
          return true;
        } else if (this.__distinctValues.indexOf(modelItem.get(this.getDelegateFilterPropertyName())) >= 0) {
          return true;
        }
        return false;
      }
      return true;
    }
  }
});