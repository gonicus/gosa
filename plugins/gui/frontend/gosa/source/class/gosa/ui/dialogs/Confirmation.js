/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

/**
* Simple confirmation dialog, which asks the user to confirm or discard the message.
*/
qx.Class.define("gosa.ui.dialogs.Confirmation", {
  extend: gosa.ui.dialogs.Dialog,

  construct: function(title, msg, type)
  {
    this.base(arguments, title);

    if (msg) {
      var message = new qx.ui.basic.Label(msg).set({
        rich : true,
        wrap : true
      });
      this.addElement(message);
    }

    var buttonAppearance = "button-primary";

    if(type && type === "warning") {
      this.setAppearance("window-warning");
      buttonAppearance = "button-warning";
    }

    var ok = this._okButton = gosa.ui.base.Buttons.getOkButton();
    ok.setAppearance(buttonAppearance);
    ok.setLabel(this.tr("Yes"));
    ok.addListener("execute", function() {
      this.fireDataEvent("confirmed", true);
      this.close();
    }, this);
    this.addButton(ok);

    var cancel = this._cancelButton = gosa.ui.base.Buttons.getCancelButton();
    cancel.setAppearance(buttonAppearance);
    cancel.setLabel(this.tr("No"));
    this.addButton(cancel);

    cancel.addListener("execute", function() {
      this.fireDataEvent("confirmed", false);
      this.close();
    }, this);
  },

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events: {
    "confirmed": "qx.event.type.Data"
  },

  members : {
    _okButton : null,
    _cancelButton : null
  },

  destruct : function() {
    this._disposeObjects("_okButton", "cancelButton");
  }
});
