/*========================================================================

 This file is part of the GOsa project -  http://gosa-project.org

 Copyright:
 (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

 License:
 LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

 See the LICENSE file in the project's top-level directory for details.

 ======================================================================== */

qx.Class.define("gosa.ui.basic.StatusLabel", {

  extend: qx.ui.basic.Label,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function(value) {
    this.base(arguments, value);
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {

    appearance: {
      refine: true,
      init: "statusLabel"
    },

    rich: {
      refine: true,
      init: true
    },

    wrap: {
      refine: true,
      init: true
    }

  }

});
