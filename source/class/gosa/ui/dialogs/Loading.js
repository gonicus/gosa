/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.dialogs.Loading",
{
  extend : gosa.ui.dialogs.Dialog,

  construct : function()
  {
    this.base(arguments, "GOsa - " + this.tr("Initializing") + "...");
    this.label = new qx.ui.basic.Label();
    this.add(this.label);
  },

  members: {
    label: null,
    setLabel: function(action){
      this.label.setValue(action);
    }
  }
});

