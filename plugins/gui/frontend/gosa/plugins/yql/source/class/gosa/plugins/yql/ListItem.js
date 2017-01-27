/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* RSS-Feed entry list item
*/
qx.Class.define("gosa.plugins.yql.ListItem", {
  extend : qx.ui.core.Widget,
  implement : [qx.ui.form.IModel],
  include : [qx.ui.form.MModelProperty],

  /**
   * @param label {String} Label to use
   * @param icon {String?null} Icon to use
   * @param model {String?null} The items value
   */
  construct : function(label, icon, model) {
    this.base(arguments);
    if (model != null) {
      this.setModel(model);
    }

    this._setLayout(new qx.ui.layout.VBox());
    this.addListener("tap", this._onTap, this);
  },
    
  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    appearance : {
      refine : true,
      init : "yql-listitem"
    },

    label : {
      apply : "_applyLabel",
      nullable : true,
      check : "String"
    },

    description: {
      check: "String",
      nullable: true,
      apply: "_applyDescription"
    },

    link: {
      check: "String",
      nullable: true
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {

    _forwardStates: {
      selected: false
    },

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "label":
          control = new qx.ui.basic.Label(this.getLabel());
          control.setRich(true);
          control.setSelectable(false);
          this._addAt(control, 0);
          if (this.getLabel() === null) {
            control.exclude();
          }
          break;

        case "description":
          control = new qx.ui.basic.Label(this.getDescription());
          control.setAnonymous(true);
          if (this.getDescription() === null) {
            control.exclude();
          }
          control.set({
            rich: true,
            wrap: true,
            selectable: false
          });
          this._addAt(control, 1);
          break;
      }

      return control || this.base(arguments, id);
    },

    // property apply
    _applyLabel : function(value)
    {
      var label = this.getChildControl("label");
      if (label) {
        label.setValue(value);
        label.show();
      } else {
        label.exclude();
      }
    },

    // property apply
    _applyDescription: function(value) {
      var control = this.getChildControl("description");
      if (value) {
        control.setValue(value);
        control.show();
      } else {
        control.exclude();
      }
    },

    _onTap: function() {
      if (this.getLink()) {
        window.open(this.getLink(), "_blank");
      }
    }
  }
});