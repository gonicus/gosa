/* ************************************************************************

   Copyright: Cajus Pollmeier <pollmeier@gonicus.de>

   License:

   Authors:

************************************************************************ */

/* ************************************************************************

#asset(cute/*)

************************************************************************ */

qx.Class.define("cute.view.Settings",
{
  extend : qx.ui.tabview.Page,

  construct : function()
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", cute.Config.getImagePath("apps/settings.png", 32));
    this._excludeChildControl("label");
    this.setLayout(new qx.ui.layout.VBox(5));
  }
});
