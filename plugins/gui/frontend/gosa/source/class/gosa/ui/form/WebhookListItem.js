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



qx.Class.define("gosa.ui.form.WebhookListItem", {
  extend: qx.ui.core.Widget,
  implement : [qx.ui.form.IModel],
  include : [qx.ui.form.MModelProperty],

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function() {
    this.base(arguments);
    this._setLayout(new qx.ui.layout.VBox());
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    appearance :
    {
      refine : true,
      init : "gosa-listitem-webhook"
    },

    label: {
      check: "String",
      nullable: true,
      apply: "_applyLabel"
    },

    mimeType: {
      check: "String",
      nullable: true,
      apply: "_applyMimeType"
    },

    secret: {
      check: "String",
      nullable: true,
      apply: "_applySecret"
    },

    expanded: {
      check: "Boolean",
      init: false,
      apply: "_applyExpanded"
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

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "label":
          control = new qx.ui.basic.Label();
          control.setAnonymous(true);
          this._addAt(control, 0);
          break;

        case "mime-type":
          control = new qx.ui.basic.Label();
          control.setAnonymous(true);
          this._addAt(control, 1);
          break;

        case "expansion":
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox());
          control.setAnonymous(true);
          control.exclude();
          this._addAt(control, 2);
          break;

        case "secret":
          control = new qx.ui.basic.Label();
          control.setSelectable(true);
          this.getChildControl("expansion").addAt(control, 0);
          break;
      }

      return control || this.base(arguments, id);
    },

    _applyExpanded: function(value) {
      if (value === true) {
        this.getChildControl("expansion").show();
      } else {
        this.getChildControl("expansion").exclude();
      }
    },

    // property apply
    _applyMimeType: function(value) {
      this.__handleValue(this.getChildControl("mime-type"), value);
    },

    // property apply
    _applyLabel: function(value) {
      this.__handleValue(this.getChildControl("label"), value);
    },

    // property apply
    _applySecret: function(value) {
      this.__handleValue(this.getChildControl("secret"), value);
    },

    // property apply
    _applyListItemType: function(value) {
      if (value === "group") {
        this.setAppearance("gosa-listitem-webhook-group");
        this.setEnabled(false);
      } else {
        this.setAppearance("gosa-listitem-webhook");
        this.setEnabled(true);
      }
    },

    __handleValue: function(control, value) {
      if (value) {
        control.setValue(value);
        control.show();
      } else {
        control.exclude();
      }
    }
  }
});