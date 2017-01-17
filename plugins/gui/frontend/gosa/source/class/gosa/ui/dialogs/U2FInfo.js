/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/*
#asset(gosa/*)
*/
qx.Class.define("gosa.ui.dialogs.U2FInfo", {

  extend: gosa.ui.dialogs.Dialog,

  construct: function()
  {
    this.base(arguments, this.tr("Performing U2F action"));
    
    var message = new qx.ui.basic.Label(this.tr("Please touch the flashing U2F device now."));
    this.addElement(message);

    this.addElement(new qx.ui.basic.Label(this.tr("You may be prompted to allow the site permission to access your security keys. After granting permission, the device will start to blink.")));


    var abort = gosa.ui.base.Buttons.getCancelButton();
    abort.addListener("execute", this.close, this);
    this.addButton(abort);
  }

});
