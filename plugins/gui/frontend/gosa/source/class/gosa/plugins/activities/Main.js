/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2016 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* Dashboard widget that shows the last changed objects
*/
qx.Class.define("gosa.plugins.activities.Main", {
  extend : qx.ui.core.Widget,
  implement: gosa.plugins.IPlugin,
  
  construct : function() {
    this.base(arguments);
    this._setLayout(new qx.ui.layout.VBox());
  },
    
  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    /**
     * Maximum number of items to show
     */
    maxItems: {
      check: "Number",
      init: 10
    }
  },
    
  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {

    draw: function(parent) {
      this._add(new qx.ui.basic.Label("Heureka, this is a dashboard widget"));
    }
  },

  defer: function () {
    gosa.view.Dashboard.registerWidget("activities", gosa.plugins.activities.Main);
  }
});