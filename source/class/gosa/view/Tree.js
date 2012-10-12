/* ************************************************************************

   Copyright: Cajus Pollmeier <pollmeier@gonicus.de>

   License:

   Authors:

************************************************************************ */

/* ************************************************************************

#asset(gosa/*)

************************************************************************ */

qx.Class.define("gosa.view.Tree",
{
  extend : qx.ui.tabview.Page,

  construct : function()
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", gosa.Config.getImagePath("apps/tree.png", 32));
    this._excludeChildControl("label");
    this.setLayout(new qx.ui.layout.VBox(5));
  }

});
