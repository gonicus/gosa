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

qx.Class.define("gosa.ui.dialogs.RpcError", {

  extend: gosa.ui.dialogs.Dialog,

  construct: function(msg)
  {
    this.base(arguments, this.tr("Error"));

    var message = new qx.ui.basic.Label(msg);
    this.addElement(message);

    var ok = gosa.ui.base.Buttons.getOkButton();
    ok.addListener("execute", this.close, this);
    this.addButton(ok);

    // var retry = gosa.ui.base.Buttons.getButton(this.tr("Retry"), "actions/dialog-retry.png");
    // retry.addListener("execute", function(){
    //     this.close();
    //     this.fireEvent("retry");
    // }, this);
    // this.addButton(retry);
  },

  events: {
    "retry" : "qx.event.type.Event"
  }
});
