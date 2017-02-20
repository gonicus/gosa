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
* Show and edit the registered webhooks.
*/
qx.Class.define("gosa.ui.settings.Webhooks", {
  extend : qx.ui.core.Widget,
  type: "singleton",

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function() {
    this.base(arguments);
    this._setLayout(new qx.ui.layout.VBox());

    this._createChildControl("title");

    this.addListenerOnce("appear", this.__initList, this);
  },

  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    NAMESPACE: "gosa.webhooks"
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
        case "title":
          control = new qx.ui.basic.Label(this.tr("Webhooks"));
          this._add(control);
          break;

        case "list":
          control = new qx.ui.form.List();
          this._add(control, {flex: 1});
          break;
      }

      return control || this.base(arguments, id);
    },

    __initList: function() {
      var list = this.getChildControl("list");
      var controller = this._listController = new qx.data.controller.List(null, list);

      controller.setDelegate({
        createItem: function() {
          return new gosa.ui.form.WebhookListItem();
        },

        bindItem: function(controller, item, index) {
          controller.bindProperty("", "model", null, item, index);
          controller.bindProperty("name", "label", null, item, index);
          controller.bindProperty("contentType", "contentType", null, item, index);
          controller.bindProperty("secret", "secret", null, item, index);
          controller.bindProperty("expanded", "expanded", null, item, index);
        }
      });

      list.addListener("changeSelection", function() {
        var selected = list.getSelection()[0].getModel();
        controller.getModel().forEach(function(child) {
          child.setExpanded(child === selected);
        }, this);
      }, this);

      var handler = gosa.data.SettingsRegistry.getHandlerForPath(gosa.ui.settings.Webhooks.NAMESPACE);
      var itemInfos = handler.getItemInfos();
      var values = new qx.data.Array();
      Object.getOwnPropertyNames(itemInfos).forEach(function(path) {

        var webhook = new gosa.core.Webhook(path, itemInfos[path]['value']);
        values.push(webhook);
      }, this);
      controller.setModel(values);
    }
  },

  defer: function(statics) {
    gosa.data.SettingsRegistry.registerEditor(statics.NAMESPACE, statics.getInstance());
  }
});