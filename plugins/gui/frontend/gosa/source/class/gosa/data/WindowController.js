/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Simple controller that holds an array of all currently opened windows
 */
qx.Class.define("gosa.data.WindowController", {
  extend: qx.core.Object,
  type: "singleton",

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function() {
    this.base(arguments);
    this.__windows = new qx.data.Array();
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __windows: null,

    getWindows: function() {
      return this.__windows;
    },

    addWindow: function(window, widget) {
      this.__windows.push(new qx.data.Array([window, widget]));
    },

    removeWindow: function(window) {
      var index = this.__findEntryByWindow(window);
      if (index >= 0) {
        this.__windows.removeAt(index);
      }
    },

    __findEntryByWindow: function(window) {
      var index = -1;
      this.__windows.some(function(tuple, idx) {
        if (tuple.getItem(0) === window) {
          index = idx;
          return true;
        }
      }, this);
      return index;
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this._disposeArray("__windows", "__widgets");
  }
});