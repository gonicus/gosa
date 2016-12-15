/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2016 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* Interface for all plugins that can be loaded via qx.io.PartLoader
*/
qx.Interface.define("gosa.plugins.IPlugin", {
  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {

    /**
     * Creates the widget and adds it to the given parent
     * @parent {qx.ui.core.Widget}
     */
    draw: function(parent) {

    }
  }
});