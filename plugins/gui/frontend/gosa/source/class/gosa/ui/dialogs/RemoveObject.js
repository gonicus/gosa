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
#asset(gosa/*)
*/
qx.Class.define("gosa.ui.dialogs.RemoveObject", {

  extend: gosa.ui.dialogs.Dialog,

  construct: function(dn)
  {
    this.base(arguments, this.tr("Remove object"));

    this.setWidth(400);

    //var text = qx.lang.String.format(this.tr("Do you want to remove this %1 object including all of its references to other objects?"), [type]);
    var text = this.tr("Do you want to remove this object including all of its references to other objects?");
    var message = new qx.ui.basic.Label(text);
    message.setRich(true);
    message.setWrap(true);
    this.addElement(message);

    var ok = gosa.ui.base.Buttons.getOkButton();
    this.addButton(ok);

    var cancel = gosa.ui.base.Buttons.getCancelButton();
    this.addButton(cancel);
    ok.addListener("click", function(){
        this.fireEvent("remove");
        this.close();
      }, this);
    cancel.addListener("click", this.close, this);
  }, 

  events: {
    "remove": "qx.event.type.Event"
  }

});
