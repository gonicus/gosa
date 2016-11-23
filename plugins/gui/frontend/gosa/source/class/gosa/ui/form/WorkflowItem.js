/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2016 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* Display a workflow item with icon, label and description
*/
qx.Class.define("gosa.ui.form.WorkflowItem", {

  extend : qx.ui.form.Button,
  
  construct : function() {
    this.base(arguments);

    var icon = this.getChildControl("icon");
    icon.setScale(true);
  },
    
  properties : {

    appearance: {
      refine: true,
      init: "gosa-workflow-item"
    },

    id: {
      check: "String"
    },

    description: {
      check: "String",
      nullable: true,
      apply: "_applyDescription"
    },

    iconSize: {
      check: "Number",
      themeable: true,
      init: 40,
      apply: "_applyIconSize"
    }
  },
    
  members : {

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "description":
          control = new qx.ui.basic.Label();
          control.setAnonymous(true);
          control.setRich(true);
          control.setWrap(true);
          this._addAt(control, 2);
          break;
      }

      return control || this.base(arguments, id);
    },

    _applyDescription: function(value, old) {
      this.setToolTipText(value);
    },

    // property apply
    _applyIconSize: function(size) {
      this.getChildControl("icon").setWidth(size);
      this.getChildControl("icon").setHeight(size);
    }
  }
});