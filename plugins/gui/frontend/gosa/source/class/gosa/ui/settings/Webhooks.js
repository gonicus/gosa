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

    this.addListenerOnce("appear", this.__initList, this);
  },

  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    NAMESPACE: "gosa.webhooks",
    URL: null
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

        case "control-bar":
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox());
          this._add(control);
          break;

        case "add-button":
          control = new qx.ui.form.Button(this.tr("Add"), "@Ligature/edit/22");
          control.addListener("execute", this._registerNewWebhook, this);
          this.getChildControl("control-bar").add(control);
          break;

        case "remove-button":
          control = new qx.ui.form.Button(this.tr("Remove"), "@Ligature/trash/22");
          control.setEnabled(false);
          control.addListener("execute", this._removeSelectedWebhook, this);
          this.getChildControl("control-bar").add(control);
          break;
      }

      return control || this.base(arguments, id);
    },

    __initList: function() {
      var promises = [gosa.io.Rpc.getInstance().cA("getWebhookUrl"), gosa.io.Rpc.getInstance().cA("getAvailableMimeTypes")];

      qx.Promise.all(promises).spread(function(result, types) {
        gosa.ui.settings.Webhooks.URL = result;
        this._createChildControl("title");
        var list = this.getChildControl("list");
        this._createChildControl("add-button");
        this._createChildControl("remove-button");
        var controller = this._listController = new gosa.data.controller.EnhancedList(null, list);

        controller.setDelegate({
          createItem: function() {
            return new gosa.ui.form.WebhookListItem();
          },

          bindItem: function(controller, item, index) {
            controller.bindProperty("", "model", null, item, index);
            controller.bindProperty("name", "label", null, item, index);
            controller.bindProperty("mimeType", "mimeType", null, item, index);
            controller.bindProperty("secret", "secret", null, item, index);
            controller.bindProperty("expanded", "expanded", null, item, index);
          },

          group: function(item) {
            return types[item.getMimeType()];
          }
        });

        list.addListener("changeSelection", function() {
          var selection = list.getSelection();
          this.getChildControl("remove-button").setEnabled(selection.length > 0);
          var selected = selection.length > 0 ? selection[0].getModel() : null;
          controller.getModel().forEach(function(child) {
            child.setExpanded(child === selected);
          }, this);
        }, this);

        this.__updateList();

      }, this);
    },

    __updateList: function() {
      var handler = gosa.data.SettingsRegistry.getHandlerForPath(gosa.ui.settings.Webhooks.NAMESPACE);
      var itemInfos = handler.getItemInfos();
      var values = new qx.data.Array();
      Object.getOwnPropertyNames(itemInfos).forEach(function(path) {
        var webhook = new gosa.core.Webhook(path, itemInfos[path]['value']);
        values.push(webhook);
      }, this);
      this._listController.setModel(values);
    },

    /**
     * Query current webhooks from backend
     */
    _refreshList: function() {
      gosa.data.SettingsRegistry.refresh(gosa.ui.settings.Webhooks.NAMESPACE).then(this.__updateList, this);
    },

    _registerNewWebhook: function() {
      var dialog = new gosa.ui.dialogs.RegisterWebhook();
      dialog.addListenerOnce("registered", function() {
        this._refreshList();
      }, this);
      dialog.open();
    },

    _removeSelectedWebhook: function() {
      var list = this.getChildControl("list");
      var selected = list.getSelection()[0].getModel();
      var dialog = new gosa.ui.dialogs.Confirmation(
        this.tr("Remove webhook"),
        this.tr("Are you sure that you want to delete this webhook? Please make sure that there are no services left using this webhook."),
        "warning"
      );
      dialog.addListenerOnce("confirmed", function() {
        gosa.io.Rpc.getInstance().cA("unregisterWebhook", selected.getName(), selected.getMimeType())
        .then(this._refreshList, this)
        .catch(gosa.ui.dialogs.Error.show);
      }, this);
      dialog.open();
    }
  },

  defer: function(statics) {
    gosa.data.SettingsRegistry.registerEditor(statics.NAMESPACE, statics.getInstance());
  }
});