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

    this._setLayout(new qx.ui.layout.HBox());
    this.addListener("tap", this._onTap, this);

    this.addListener("pointerover", this._onPointerOver, this);
    this.addListener("pointerout", this._onPointerOut, this);
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
    },

    /** Any URI String supported by qx.ui.basic.Image to display an icon */
    icon :
    {
      check : "String",
      apply : "_applyIcon",
      nullable : true,
      themeable : true
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {

    _forwardStates: {
      selected: false,
      hovered : true
    },

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "icon":
          control = new qx.ui.basic.Image(this.getIcon());
          control.setAnonymous(true);
          this._addAt(control, 0);
          if (this.getIcon() == null) {
            control.exclude();
          }
          break;

        case "content":
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox());
          control.setAnonymous(true);
          control.setAllowGrowX(false);
          this._addAt(control, 1, {flex: 1});
          break;

        case "label":
          control = new qx.ui.basic.Label(this.getLabel());
          control.setRich(true);
          control.setSelectable(false);
          this.getChildControl("content").addAt(control, 0);
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
          this.getChildControl("content").addAt(control, 1);
          break;
      }

      return control || this.base(arguments, id);
    },

    // property apply
    _applyIcon : function(value)
    {
      var icon = this.getChildControl("icon");
      console.log("applyIcon");
      console.log(value);
      if (icon) {
        icon.setSource(value);
        icon.show();
      }
      else {
        icon.exclude();
      }
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
    },

    /**
     * Event handler for the pointer over event.
     */
    _onPointerOver : function() {
      this.addState("hovered");
    },


    /**
     * Event handler for the pointer out event.
     */
    _onPointerOut : function() {
      this.removeState("hovered");
    }
  },

  destruct : function() {
    this.removeListener("pointerover", this._onPointerOver, this);
    this.removeListener("pointerout", this._onPointerOut, this);
  }
});