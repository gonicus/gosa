/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.dialogs.Loading",
{
  extend : gosa.ui.dialogs.Dialog,

  construct : function()
  {
    this.base(arguments);
    this.getChildControl("captionbar").exclude();
    this.getChildControl("title").exclude();
    this.resetMinHeight();
    this.resetMinWidth();
    this._buttonPane.exclude();

    var label = new qx.ui.basic.Label(this.tr("Initializing") + "...");
    label.setPadding([10, 28]);
    this.add(label);

    this.addListenerOnce("resize", this.center, this);
  }
});

