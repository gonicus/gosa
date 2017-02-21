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
      nullable: true
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

        case "expansion":
          control = new qx.ui.container.Composite(new qx.ui.layout.Grid(5, 5));
          control.setAnonymous(true);
          control.exclude();
          this._addAt(control, 2, {flex: 1});
          break;

        case "hint":
          var headers = '<ul><li><strong>Content-Type:</strong> <i>'+
                        this.getMimeType()+'</i></li><li><strong>HTTP_X_HUB_SENDER:</strong> <i>'+
                        this.getLabel()+'</i></li><li><strong>HTTP_X_HUB_SIGNATURE:</strong> '+
                        this.tr("SHA-512 hash of the content body encrypted with secret:")+' <i>'+this.getSecret()+'</i></li></ul>';
          var msg = this.tr("Use the following headers when you POST data to %1", "<strong>"+gosa.ui.settings.Webhooks.URL+"</strong>");
          msg += headers;
          control = new qx.ui.basic.Label(msg).set({rich: true, wrap: true});
          this.getChildControl("expansion").add(control, {row: 0, column: 0});
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
    _applyLabel: function(value) {
      this.__handleValue(this.getChildControl("label"), value);
    },

    // property apply
    _applySecret: function() {
      if (!this.hasChildControl("hint")) {
        this._createChildControl("hint");
      }
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