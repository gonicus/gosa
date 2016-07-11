/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.data.model.SearchResultItem",
{
  extend : qx.core.Object,

  properties : {

    title : {
      check : "String",
      event : "changeTitle"
    },

    dn : {
      check : "String",
      event : "changeDn"
    },

    uuid : {
      check : "String",
      event : "changeUuid"
    },

    type : {
      check : "String",
      event : "changeType"
    },

    relevance : {
      check : "Integer",
      event : "changeRelevance"
    },

    lastChanged : {
      check : "Integer",
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
      nullable: true
    },

    actions : {
      check : "Array",
      event : "changeActions",
      nullable: true
    },

    icon : {
      check : "String",
      event : "changeIcon",
      nullable: true
    }
  },


  members : {
    toString: function() {
      return this.getDn();
    }
  }

});
