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
* Basic data structure for a webhook
*/
qx.Class.define("gosa.core.Webhook", {
  extend : qx.core.Object,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function(path, value) {
    this.base(arguments);
    var parts = path.split("###");
    this.setContentType(parts[0]);
    this.setName(parts[1]);
    this.setSecret(value);
  },
  
  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    name: {
      check: "String",
      init: "",
      event: "changeName"
    },
    contentType: {
      check: "String",
      init: "",
      event: "changeContentType"
    },
    secret: {
      check: "String",
      nullable: true,
      event: "changeSecret"
    },
    expanded: {
      check: "Boolean",
      init: false,
      event: "changeExpanded"
    }
  }
});