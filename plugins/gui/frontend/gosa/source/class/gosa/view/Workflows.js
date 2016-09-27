/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/* ************************************************************************

#asset(gosa/*)

************************************************************************ */

qx.Class.define("gosa.view.Workflows",
{
  extend : qx.ui.tabview.Page,

  construct : function()
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", "@FontAwesome/f0c3");
    this.getChildControl("button").getChildControl("label").exclude();
    this.setLayout(new qx.ui.layout.VBox(5));
  }

});
