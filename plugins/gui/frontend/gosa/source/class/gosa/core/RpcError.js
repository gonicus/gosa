/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* Extend {Error} class to provide access to the orginal error data
*/
qx.Class.define("gosa.core.RpcError", {
  extend : Error,
  
  construct : function(data) {
    var inst = Error.call(this, data.message);
    // map stack trace properties since they're not added by Error's constructor
    if (inst.stack) {
      this.stack = inst.stack;
    }
    if (inst.stacktrace) {
      this.stacktrace = inst.stacktrace;
    }

    this.__data = data;
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __data : null,

    /**
     * Returns the error message.
     *
     * @return {String} error message
     */
    toString : function() {
      return this.__data.message;
    },

    getData: function() {
      return this.__data;
    }
  }
});