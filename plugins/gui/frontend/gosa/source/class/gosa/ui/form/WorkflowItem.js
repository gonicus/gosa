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

  extend : qx.ui.form.ListItem,
  
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
      apply: "_applyIconSize",
      event: "changeIconSize"
    },

    loading: {
      check: "Boolean",
      init: false,
      apply: "_applyLoading"
    },

    /**
     * How this list item should behave like group or normal ListItem
     */
    listItemType: {
      check: ['group', 'item'],
      init: 'item',
      apply: '_applyListItemType'
    }
  },
    
  members : {
    // property apply
    _applyListItemType: function(value) {
      if (value === "group") {
        this.setLayoutProperties({lineBreak: true, stretch: true, newLine: true});
        this.setAppearance("gosa-workflow-category");
      } else {
        this.setLayoutProperties({});
        this.setAppearance("gosa-workflow-item");
      }
    },

    // property apply
    _applyLoading: function(value) {
      if (value) {
        this.getChildControl("throbber").show();
      } else {
        this.getChildControl("throbber").exclude();
      }
    },

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "label":
          control = new qx.ui.basic.Label(this.getLabel());
          control.setAnonymous(true);
          control.setRich(this.getRich());
          control.setSelectable(this.getSelectable());
          this._addAt(control, 2);
          if (this.getLabel() == null || this.getShow() === "icon") {
            control.exclude();
          }
          break;

        case "throbber":
          control = new gosa.ui.Throbber();
          this.bind("iconSize", control, "size");
          control.exclude();
          control.bind("visibility", this.getChildControl("icon"), "visibility", {
            converter: function(value) {
              return ['hidden', 'excluded'].indexOf(value) >= 0 ? 'visible' : 'excluded';
            }
          });
          this._addAt(control, 1);
          break;

      }

      return control || this.base(arguments, id);
    },

    _applyDescription: function(value, old) {
      this.setToolTipText(value);
    },

    // property apply
    _applyIconSize: function(size) {
      this.getChildControl("icon").set({
        width: size,
        height: size,
        scale: true
      });
    }
  }
});