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
qx.Class.define("gosa.ui.tree.Folder", {
  extend: qx.ui.tree.TreeFolder,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function(label) {
    this._initialLabel = label;
    this.base(arguments, label);
  },

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events : {
    "changedValue": "qx.event.type.Data"
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    modified: {
      check: "Boolean",
      init: false,
      event: "changeModified"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    _initialLabel: null,

    _applyLabel: function(value, old) {
      this.base(arguments, value, old);
      this.setModified(this._initialLabel !== value);
      if (this._initialLabel !== undefined) {
        this.fireDataEvent("changedValue", value);
      }
    }
  }
});
