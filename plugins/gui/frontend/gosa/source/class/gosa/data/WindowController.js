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
      var index = -1;
      this.__windows.some(function(tuple, idx) {
        if (tuple.getItem(0) === window) {
          index = idx;
          return true;
        }
      }, this);
      if (index >= 0) {
        this.__windows.removeAt(index);
      }
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