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

/*
* This dialog warns the user that a object he is currently editing is about to be closed due to inactivity
* #asset(gosa/*)
*/
qx.Class.define("gosa.ui.dialogs.ClosingObject", {

  extend: gosa.ui.dialogs.Dialog,

  construct: function(dn, timeout)
  {
    this.base(arguments, this.tr("Object: %1", dn));
    this.setAutoDispose(true);

    var closingCountdownEnd = Date.now() + timeout*1000;
    this._timer = new qx.event.Timer(1000);
    this._timer.addListener("interval", function() {
      var remaining = Math.max(0,Math.round((closingCountdownEnd - Date.now())/1000));
      this._message.setValue(this.tr("This object will be closed in %1 seconds if you don't continue editing!", remaining));
      if (remaining <= 0) {
        this._timer.stop();
      }
    }, this);
    this._timer.start();

    var text = this.tr("This object will be closed in %1 seconds if you don't continue editing!", timeout);
    var message = this._message = new qx.ui.basic.Label(text);
    message.setRich(true);
    message.setWrap(true);
    this.addElement(message);


    this.__createOkButton();
    this.__createCancelButton();
  },

  properties : {
    //overridden
    appearance : {
      refine : true,
      init : "window-warning"
    }
  },

  events: {
    "closeObject": "qx.event.type.Event",
    "continue": "qx.event.type.Event"
  },

  members: {
    _timer : null,
    _message : null,

    __createOkButton : function() {
      var ok = gosa.ui.base.Buttons.getOkButton();
      ok.setAppearance("button-warning");
      ok.setLabel(this.tr("Continue"));
      this.addButton(ok);

      ok.addListener("click", function(){
        this.fireEvent("continue");
        this.close();
      }, this);
    },

    __createCancelButton : function() {
      var cancel = gosa.ui.base.Buttons.getCancelButton();
      cancel.setAppearance("button-warning");
      cancel.setLabel(this.tr("Close"));
      this.addButton(cancel);

      cancel.addListener("click", function() {
        this.fireEvent("closeObject");
        this.close();
      }, this);
    }
  },

  destruct: function() {
    if (this._timer) {
      this._timer.stop();
      this._timer = null;
    }
    this._message = null;
  }
});
