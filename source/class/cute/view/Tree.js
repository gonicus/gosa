/* ************************************************************************

   Copyright: Cajus Pollmeier <pollmeier@gonicus.de>

   License:

   Authors:

************************************************************************ */

/* ************************************************************************

#asset(cute/*)

************************************************************************ */

qx.Class.define("cute.view.Tree",
{
  extend : qx.ui.tabview.Page,

  construct : function()
  {
    var barWidth = 200;

    // Call super class and configure ourselfs
    this.base(arguments, "", cute.Config.getImagePath("apps/tree.png", 32));
    this._excludeChildControl("label");
    this.setLayout(new qx.ui.layout.VBox(5));
  }

});
