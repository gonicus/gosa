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

qx.Class.define("gosa.data.model.SearchResultItem", {
  extend : qx.core.Object,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function() {
    this.base(arguments);
    this.__highlightProperties = ["description", "dn"];
    this.__highlighted = {};
    // gosa.data.model.SearchResult.getInstance().bind("highlight", this, "highlight");
  },

  properties : {

    title : {
      check : "String",
      event : "changeTitle"
    },

    dn : {
      check : "String",
      event : "changeDn",
      apply: "_applyHighlight"
    },

    uuid : {
      check : "String",
      event : "changeUuid"
    },

    type : {
      check : "String",
      event : "changeType",
      apply : "_applyType"
    },

    relevance : {
      check : "Number",
      event : "changeRelevance"
    },

    lastChanged : {
      check : "gosa.io.types.Timestamp",
      event : "changeLastChanged"
    },

    secondary : {
      check : "Boolean",
      event : "changeSecondary"
    },

    location : {
      check : "String",
      event : "changeLocation"
    },

    extensions : {
      check : "Array",
      event : "changeExtensions",
      nullable: true
    },

    description : {
      check : "String",
      event : "changeDescription",
      nullable: true,
      apply: "_applyHighlight"
    },

    actions : {
      check : "Array",
      event : "changeActions",
      nullable: true
    },

    icon : {
      check : "String",
      event : "changeIcon",
      nullable: true,
      transform: "_transformIcon"
    },

    highlight: {
      check: "RegExp",
      nullable: true,
      transform: "_transformHighlight",
      apply: "_applyHighlight"
    }
  },


  members : {
    __typeIconUsed : null,
    __highlighted : null,
    __highlightProperties : null,
    __blockHighlighting: null,

    _transformHighlight: function(value) {
      return value ? new RegExp('(' + qx.lang.String.escapeRegexpChars(value) + ')', "ig") : null;
    },

    _applyHighlight: function(value, old, name) {
      if (!this.getHighlight() || this.__blockHighlighting) {
        return;
      }
      var properties = this.__highlightProperties;
      if (qx.lang.Array.includes(properties, name)) {
        // only highlight this property
        properties = [name];
        qx.lang.Array.remove(this.__highlighted, name);
      } else if (name !== "highlight") {
        // unhandled property
        return;
      } else {
        // highlight value has changes, renew all
        this.__highlighted = [];
      }
      this.__blockHighlighting = true;
      properties.forEach(function(prop) {
        if (this.isPropertyInitialized(prop)) {
          if (qx.lang.Array.includes(this.__highlighted, prop)) {
            // skip this one, as it is already highlighted
            return;
          }
          var currentValue = this["get"+qx.lang.String.firstUp(prop)]();
          if (!currentValue) {
            // nothing to be highlighted
            return;
          }
          this.__highlighted.push(prop);
          this["set"+qx.lang.String.firstUp(prop)](currentValue.replace(this.getHighlight(), "<b>$1</b>"));
        }
      }, this);
      this.__blockHighlighting = false;
    },


    // property apply
    _applyType: function(value) {
      if (!this.getIcon()) {
        this.__typeIconUsed = true;
        this.setIcon(gosa.util.Icons.getIconByType(value, 64));
      }
    },

    _transformIcon: function(value, old) {
      if (!value) {
        if (this.__typeIconUsed) {
          // keep old value
          return old;
        } else if (this.isPropertyInitialized("type")) {
          this.__typeIconUsed = true;
          return this.setIcon(gosa.util.Icons.getIconByType(this.getType(), 64));
        }
      }
      return value;
    },

    toString: function() {
      return this.getDn();
    }
  }

});
