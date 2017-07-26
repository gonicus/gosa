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
 * @ignore(Fuse)
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
   PROPERTIES
   *****************************************************************************
   */
  properties : {
    appearance: {
      refine: true,
      init: "webhook-editor"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    _fullTableData: null,

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {
        case "title":
          control = new qx.ui.basic.Label(this.tr("Webhooks"));
          this._add(control);
          break;

        case "table":
          var propertyEditor_resizeBehaviour = {
            tableColumnModel : function(obj) {
              return new qx.ui.table.columnmodel.Resize(obj);
            }
          };
          control = new qx.ui.table.Table(null, propertyEditor_resizeBehaviour);
          control.setColumnVisibilityButtonVisible(false);
          control.setRowHeight(30);

          this._addAt(control, 2, {flex: 1});
          break;

        case "toolbar":
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox(16));
          control.add(this.getChildControl("search-field"), {flex: 1});

          var buttons = new qx.ui.toolbar.Part();
          buttons.add(this.getChildControl("action-menu-button"));
          control.add(buttons);
          this._add(control);
          break;

        case "action-menu-button":
          control = new qx.ui.toolbar.MenuButton(this.tr("Action"));
          control.setMenu(this.getChildControl("action-menu"));
          break;

        case "open-button":
          control = new qx.ui.menu.Button(this.tr("Show details"), "@Ligature/view");
          control.setEnabled(false);
          control.addListener("execute", this._onOpenObject, this);
          break;

        case "create-button":
          control = new qx.ui.menu.Button(this.tr("Create..."), "@Ligature/edit");
          control.addListener("execute", this._registerNewWebhook, this);
          break;

        case "delete-button":
          control = new qx.ui.menu.Button(this.tr("Delete"), "@Ligature/trash");
          control.setEnabled(false);
          control.addListener("execute", this._removeSelectedWebhook, this);
          break;

        case "action-menu":
          control = new qx.ui.menu.Menu();
          control.add(this.getChildControl("open-button"));
          control.add(this.getChildControl("create-button"));
          control.add(this.getChildControl("delete-button"));
          break;

        case "search-field":
          control = new qx.ui.form.TextField().set({
            placeholder : this.tr("Search..."),
            liveUpdate : true,
            allowGrowX : true
          });
          control.addListener("changeValue", this.__doFilter, this);
          break;
      }

      return control || this.base(arguments, id);
    },

    __initList: function() {
      var promises = [gosa.io.Rpc.getInstance().cA("getWebhookUrl"), gosa.io.Rpc.getInstance().cA("getAvailableMimeTypes")];

      qx.Promise.all(promises).spread(function(result, types) {
        gosa.ui.settings.Webhooks.URL = result;
        this._createChildControl("title");
        this._createChildControl("toolbar");
        var table = this.getChildControl("table");

        // create table
        var tableModel = new qx.ui.table.model.Simple();
        tableModel.setColumns([
          this.tr('Name'),
          this.tr('Mime-Type'),
          this.tr('Format')
        ]);

        table.setTableModel(tableModel);
        table.getSelectionModel().setSelectionMode(qx.ui.table.selection.Model.SINGLE_SELECTION);
        table.addListener('dblclick', this._onOpenObject, this);
        table.getSelectionModel().addListener("changeSelection", this._onChangeSelection, this);

        table.setContextMenuHandler(0, this._contextMenuHandlerRow, this);
        table.setContextMenuHandler(1, this._contextMenuHandlerRow, this);
        table.setContextMenuHandler(2, this._contextMenuHandlerRow, this);

        this.__updateList();

        tableModel.sortByColumn(0, true);
      }, this);
    },

    /**
     * Context menu handler for a right-click in a row.
     *
     * @param col {Integer}
     *   The number of the column in which the right click was issued.
     *
     * @param row {Integer}
     *   The number of the row in which the right click was issued
     *
     * @param table {qx.ui.table.Table}
     *   The table in which the right click was issued
     *
     * @param dataModel {qx.ui.table.model.Simple}
     *   Complete data model of the table
     *
     * @param contextMenu {qx.ui.menu.Menu}
     *   Menu in which buttons can be added to implement this context menu.
     */
    _contextMenuHandlerRow: function(col, row, table, dataModel, contextMenu) {
      var openButton = new qx.ui.menu.Button(this.tr("Show details"), "@Ligature/view/22");
      openButton.addListener("execute", this._onOpenObject, this);
      contextMenu.add(openButton);
      var deleteButton = new qx.ui.menu.Button(this.tr("Delete"), "@Ligature/trash/22");
      deleteButton.addListener("execute", this._removeSelectedWebhook, this);
      contextMenu.add(deleteButton);
      return true;
    },

    __updateList: function() {

      var handler = gosa.data.SettingsRegistry.getHandlerForPath(gosa.ui.settings.Webhooks.NAMESPACE);
      var itemInfos = handler.getItemInfos();
      var tableData = this._tableData = [];

      Object.getOwnPropertyNames(itemInfos).forEach(function(path) {
        var mimeType = path.replace(/\+.*$/, "");
        var format = path.replace(/^[^+]*\+([^#]*)#.*$/, "$1");
        tableData.push([itemInfos[path].title, mimeType, format, itemInfos[path].value]);
      }, this);

      this.getChildControl("table").getTableModel().setData(tableData, false);
      this._fullTableData = tableData;
      this.__doFilter();
    },

    __doFilter: function() {
      var searchValue = this.getChildControl("search-field").getValue();
      if (searchValue && searchValue.length > 2) {
        var options = {
          shouldSort: false,
          threshold: 0.4,
          tokenize: true,
          keys: ["0", "1"]
        };

        var tableData = this.getChildControl("table").getTableModel().getData();
        var fuse = new Fuse(tableData, options);
        tableData = fuse.search(searchValue);
        this.getChildControl("table").getTableModel().setData(tableData, false);

      } else {
        this.getChildControl("table").getTableModel().setData(this._fullTableData, false);
      }

    },

    _onOpenObject : function()
    {
      var table = this.getChildControl("table");
      var selection = table.getSelectionModel();
      if (selection.getSelectedCount() > 0) {
        selection.iterateSelection(function(index) {
          var row = table.getTableModel().getRowData(index);
          var name = row[0];
          var mime = row[1] + "+" + row[2];
          var secret = row[3];

          var msg = this.tr("The emitter of packages for this webhook must use this data:") + "<br><br><table>";
          msg += '<tr><td><strong>URL</strong></td><td><i>'+ gosa.ui.settings.Webhooks.URL + "</i></td></tr>";
          msg += '<tr><td><strong>Content-Type</strong></td><td><i>' + mime + "</i></td></tr>";
          msg += '<tr><td><strong>Secret</strong></td><td><i>'+ secret + "</i></td></tr>";
          msg += '<tr><td><strong>HTTP_X_HUB_SENDER</strong></td><td><i>' + name + "</i></td></tr>";
          msg += '<tr><td><strong>HTTP_X_HUB_SIGNATURE</strong></td><td><i>' +
                 this.tr("SHA-512, secret encrypted hash of the content body") + "</i></td></tr></table>";

          var dialog = new gosa.ui.dialogs.Info(msg);
          dialog.open();
        }, this);
      }
    },

    _onChangeSelection: function(ev) {
      var selectionModel = ev.getTarget();

      if (selectionModel.getSelectedCount() > 0) {
        this.getChildControl("open-button").setEnabled(true);
        this.getChildControl("delete-button").setEnabled(true);
      }
      else {
        this.getChildControl("open-button").setEnabled(false);
        this.getChildControl("delete-button").setEnabled(false);
      }
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
      var table = this.getChildControl("table");
      var selection = table.getSelectionModel();
      if (selection.getSelectedCount() > 0) {
        selection.iterateSelection(function(index) {
          var row = table.getTableModel().getRowData(index);
          var name = row[0];
          var mime = row[1] + "+" + row[2];

          var dialog = new gosa.ui.dialogs.Confirmation(
          this.tr("Delete webhook"),
          this.tr("Please make sure that there are no services left using this webhook.") + "<br><br>" +
          this.tr("Are you sure that you want to delete this webhook?"),
          "warning"
          );
          dialog.addListenerOnce("confirmed", function(ev) {
            if (ev.getData()) {
              gosa.io.Rpc.getInstance().cA("unregisterWebhook", name, mime)
              .then(this._refreshList, this)
              .catch(gosa.ui.dialogs.Error.show);
            }
          }, this);
          dialog.open();
        }, this);
      }
    }
  },

  defer: function(statics) {
    gosa.data.SettingsRegistry.registerEditor(statics.NAMESPACE, statics.getInstance());
  }
});