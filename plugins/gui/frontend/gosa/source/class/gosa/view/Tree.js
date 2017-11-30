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
* @ignore(Fuse)
*/
qx.Class.define("gosa.view.Tree", {
  extend : qx.ui.tabview.Page,
  type: "singleton",

  construct : function()
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", "@Ligature/sitemap");
    this._createChildControl("bread-crumb");
    this.getChildControl("button").getChildControl("label").exclude();
    this.setLayout(new qx.ui.layout.Canvas());
    this.addListenerOnce("appear", this.load, this);
    this._rpc = gosa.io.Rpc.getInstance();
    this._objectRights = {};

    this.__debouncedReload = qx.util.Function.debounce(this.__reloadTree, 500, true);
    gosa.io.Sse.getInstance().addListener("objectRemoved", this.__debouncedReload, this);
    gosa.io.Sse.getInstance().addListener("objectCreated", this.__debouncedReload, this);
    gosa.io.Sse.getInstance().addListener("objectModified", this.__debouncedReload, this);
    gosa.io.Sse.getInstance().addListener("objectMoved", this.__debouncedReload, this);
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    appearance : {
      refine: true,
      init: "tree-view"
    }
  },

  members : {
    _objectRights : null,
    _rpc : null,
    _tableData : null,
    __debouncedReload: null,

    _createChildControlImpl : function(id, hash) {

      var control = null;

      switch(id) {
        case "bread-crumb":
          control = new gosa.ui.indicator.BreadCrumb();
          control.addListener("selected", function(ev) {
            this.getChildControl("tree").getSelection().setItem(0, ev.getData());
          }, this);
          this.add(control, {top : 0, left: 0, right: 0});
          break;

        case "tree":
          var root = new gosa.data.model.TreeResultItem(this.tr("Root"));
          root.setType("root");     // Required to show the icon
          root.load();

          control = new qx.ui.tree.VirtualTree(root, "title", "children");
          control.setSelectionMode("one");
          this.__applyTreeDelegate(control);
          this.getChildControl("splitpane").add(control, 1);
          // Act on tree selection to automatically update the list
          control.getSelection().addListener("change", this.__refreshTable, this);
          break;

        case "splitpane":
          control = new qx.ui.splitpane.Pane("horizontal");
          this.add(control, {top : 46, left: 0, right: 0, bottom: 0});
          break;

        case "listcontainer":
          control = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
          control.add(this.getChildControl("toolbar"), { top   : 0, left  : 0, right : 0 });
          this.getChildControl("splitpane").add(control, 2);
          break;

        case "toolbar":
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox(16));
          control.add(this.getChildControl("search-field"), {flex: 1});

          var buttons = new qx.ui.toolbar.Part();
          buttons.add(this.getChildControl("action-menu-button"));
          buttons.add(this.getChildControl("create-menu-button"));
          buttons.add(this.getChildControl("filter-menu-button"));

          control.add(buttons);
          break;

        case "create-menu-button":
          control = new qx.ui.toolbar.MenuButton(this.tr("Create"));
          control.setMenu(this.getChildControl("create-menu"));
          break;

        case "filter-menu-button":
          control = new qx.ui.toolbar.MenuButton(this.tr("Show"));
          control.setMenu(this.getChildControl("filter-menu"));
          break;

        case "action-menu-button":
          control = new qx.ui.toolbar.MenuButton(this.tr("Action"));
          control.setEnabled(false);
          control.setMenu(this.getChildControl("action-menu"));
          break;

        case "search-field":
          control = new qx.ui.form.TextField().set({
            placeholder : this.tr("Search..."),
            liveUpdate : true,
            allowGrowX : true
          });
          control.setEnabled(false);
          control.addListener("changeValue", this._applyFilter, this);
          break;

        case "create-menu":
          control = new qx.ui.menu.Menu();
          break;

        case "filter-menu":
          control = new qx.ui.menu.Menu();
          break;

        case "open-button":
          control = new qx.ui.menu.Button(this.tr("Edit"), "@Ligature/edit");
          control.setEnabled(false);
          control.addListener("execute", this._onOpenObject, this);
          break;

        case "delete-button":
          control = new qx.ui.menu.Button(this.tr("Delete"), "@Ligature/trash");
          control.setEnabled(false);
          control.addListener("execute", this._onDeleteObject, this);
          break;

        case "move-button":
          control = new qx.ui.menu.Button(this.tr("Move"), "@Ligature/move");
          control.setEnabled(false);
          control.addListener("execute", this._onMoveObject, this);
          break;

        case "action-menu":
          control = new qx.ui.menu.Menu();
          control.add(this.getChildControl("open-button"));
          control.add(this.getChildControl("move-button"));
          control.add(this.getChildControl("delete-button"));
          break;

        case "table":
          // Create the table
          var tableModel = this._tableModel = new qx.ui.table.model.Simple();
          tableModel.setCaseSensitiveSorting(false);
          tableModel.setColumns(["", this.tr("Name"), this.tr("Description"), this.tr("DN"), this.tr("UUID")], [
            'type',
            'title',
            'description',
            'dn',
            'uuid'
          ]);
          var customModel = {
            tableColumnModel : function(obj) {
              return new qx.ui.table.columnmodel.Resize(obj);
            }
          };

          var table = new qx.ui.table.Table(tableModel, customModel);
          table.setColumnVisibilityButtonVisible(false);
          table.setRowHeight(30);
          var toolbar = this.getChildControl("toolbar");
          var getToolbarHeight = function() {
            var bounds = toolbar.getBounds();
            if (!bounds) {
              toolbar.addListenerOnce("appear", getToolbarHeight);
              return false;
            }
            table.setLayoutProperties({top: bounds.height, left: 0, bottom: 0, right: 0});
            return true;
          };
          this.getChildControl("listcontainer").add(table, {top: 42, bottom: 0, left: 0, right: 0});
          getToolbarHeight();
          table.addListener('dblclick', this._onOpenObject, this);

          table.getSelectionModel().addListener("changeSelection", this._onChangeSelection, this);

          table.setContextMenuHandler(0, this._contextMenuHandlerRow, this);
          table.setContextMenuHandler(1, this._contextMenuHandlerRow, this);
          table.setContextMenuHandler(2, this._contextMenuHandlerRow, this);

          table.getSelectionModel().setSelectionMode(qx.ui.table.selection.Model.MULTIPLE_INTERVAL_SELECTION);
          var tcm = table.getTableColumnModel();
          var resizeBehavior = tcm.getBehavior();
          resizeBehavior.setWidth(0, 32);
          resizeBehavior.setWidth(1, "1*");
          resizeBehavior.setWidth(2, "1*");
          resizeBehavior.setWidth(3, "1*");
          tcm.setColumnVisible(3, false);
          tcm.setColumnVisible(4, false);
          tcm.setDataCellRenderer(0, new gosa.ui.table.cellrenderer.ImageByType(22, 22));
          tcm.setDataCellRenderer(2, new qx.ui.table.cellrenderer.Html());

          control = table;
          break;

        case "spinner":
          control = new gosa.ui.Throbber();
          control.addState("blocking");
          control.exclude();
          this.getChildControl("listcontainer").add(control, {edge: 0});
          break;

      }

      return control || this.base(arguments, id, hash);
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
    _contextMenuHandlerRow: function(col,
                                     row,
                                     table,
                                     dataModel,
                                     contextMenu) {
      var actionButton = new qx.ui.menu.Button(this.tr("Action"));
      actionButton.setMenu(this.getChildControl("action-menu"));
      contextMenu.add(actionButton);
      var createButton = new qx.ui.menu.Button(this.tr("Create"));
      createButton.setMenu(this.getChildControl("create-menu"));
      contextMenu.add(createButton);
      var filterButton = new qx.ui.menu.Button(this.tr("Filter"));
      filterButton.setMenu(this.getChildControl("filter-menu"));
      contextMenu.add(filterButton);

      return true;
    },

    _onChangeSelection: function(ev) {
      var selectionModel = ev.getTarget();

      if (selectionModel.getSelectedCount() > 0) {
        var canOpen = true;
        var canDelete = true;
        selectionModel.iterateSelection(function(index) {
          var selection = this._tableModel.getRowData(index);
          canOpen = canOpen && qx.lang.Array.contains(this._objectRights[selection[0]] || [], "r");
          canDelete = canDelete && qx.lang.Array.contains(this._objectRights[selection[0]] || [], "d");
        }, this);
        this.getChildControl("action-menu-button").setEnabled(canOpen && canDelete);
        this.getChildControl("open-button").setEnabled(canOpen);
        this.getChildControl("move-button").setEnabled(canOpen);
        this.getChildControl("delete-button").setEnabled(canDelete);
      } else {
        this.getChildControl("action-menu-button").setEnabled(false);
        this.getChildControl("open-button").setEnabled(false);
        this.getChildControl("move-button").setEnabled(false);
        this.getChildControl("delete-button").setEnabled(false);
      }
    },

    __applyTreeDelegate : function(tree) {
      // Special delegation handling
      var iconConverter = function(data, model, source, target) {
        if (model.isDummy()) {
          return null;
        }
        if (!model.isLoading()) {
          if (target.$$animationHandle) {
            gosa.ui.Throbber.stopAnimation(target.getChildControl('icon'), target.$$animationHandle, true);
            delete target.$$animationHandle;
          }
          if (model.getType()) {
            return gosa.util.Icons.getIconByType(model.getType(), 22);
          }
          return "@Ligature/pencil";
        } else {
          if (target.getChildControl('icon').getBounds()) {
            target.$$animationHandle = gosa.ui.Throbber.animate(target.getChildControl('icon'));
          } else {
            target.getChildControl('icon').addListenerOnce('appear', function() {
              target.$$animationHandle = gosa.ui.Throbber.animate(target.getChildControl('icon'));
            }, this);
          }
          return "@Ligature/adjust";
        }
      };

      var delegate = {

        // Bind properties from the item to the tree-widget and vice versa
        bindItem : function(controller, item, index) {
          controller.bindDefaultProperties(item, index);
          controller.bindPropertyReverse("open", "open", null, item, index);
          controller.bindProperty("open", "open", null, item, index);
          controller.bindProperty("dn", "toolTipText", null, item, index);

          // Handle images
          controller.bindProperty("type", "icon", { converter: iconConverter }, item, index);
          controller.bindProperty("loading", "icon", { converter: iconConverter }, item, index);
        }
      };
      tree.setDelegate(delegate);
    },

    load : function(){

      // Create the Tree
      this.getChildControl("tree");
      this.getChildControl("listcontainer");
      this.getChildControl("table");

     this.__refreshTable();
    },

    __updateMenus : function() {
      var selection = this.getChildControl("tree").getSelection().getItem(0);
      if (selection) {
        if (selection.getType() === "root") {
          // nothing can be added to root element, skip RPC and clear everything
          this._objectRights = {};
          this.getChildControl("create-menu").removeAll();
          this.getChildControl("filter-menu").removeAll();
          return;
        }
        // load object types
        this._rpc.cA("getAllowedSubElementsForObjectWithActions", selection.getType())
        .then(function(result) {
          this._objectRights = result;
          this.getChildControl("create-menu").removeAll();
          this.getChildControl("filter-menu").removeAll();
          var visibleTypes = {};
          this._tableModel.getData().forEach(function(item) {
            visibleTypes[item[0]] = true;
          });
          Object.getOwnPropertyNames(result).sort().forEach(function(name) {
            var allowed = result[name];
            if (allowed.includes("c")) {
              var icon = gosa.util.Icons.getIconByType(name, 22);
              var button = new qx.ui.menu.Button(this['tr'](name), icon);
              button.setAppearance("icon-menu-button");
              button.setUserData("type", name);
              this.getChildControl("create-menu").add(button);
              button.addListener("execute", this._onCreateObject, this);
            }
            if (visibleTypes[name] && allowed.includes("r")) {
              var button = new qx.ui.menu.CheckBox(this['tr'](name));
              // initially they are all selected
              button.setValue(true);
              button.setUserData("type", name);
              this.getChildControl("filter-menu").add(button);
              button.addListener("execute", this._applyFilter, this);
            }
          }, this);
        }, this).catch(function(error) {
          new gosa.ui.dialogs.Error(error).open();
        });
      }
    },

    __updateBreadCrumb : function(selection)
    {
      var item = selection.getItem(0);

      // Collect all parents
      var crumbs = [];
      do {
        crumbs.unshift(item);
        item = item.getParent();
      } while (item);


      this.getChildControl("bread-crumb").setPath(crumbs);
    },

    __refreshTable : function() {
      var sel = this.getChildControl("tree").getSelection();
      this.__updateBreadCrumb(sel);

      if (sel.length > 0) {
        this.getChildControl("create-menu-button").setEnabled(true);
        this.getChildControl("filter-menu-button").setEnabled(true);

        var done = [];
        var tableModel = this.getChildControl("table").getTableModel();

        var item = sel.getItem(0);
        item.load().then(function() {
          if (!this._tableData) {
            this._tableData = new qx.data.Array();
          } else {
            this._tableData.removeAll();
          }
          var children = item.getChildren().concat(item.getLeafs());
          children.forEach(function(child) {
            if(!qx.lang.Array.contains(done, child)){
              this._tableData.push(child.getTableRow());
              done.push(child);
            }
          }, this);
          tableModel.setDataAsMapArray(this._tableData.toArray());
          var searchField = this.getChildControl("search-field");
          searchField.setEnabled(!!this._tableData.length);
          if (searchField.getValue() && searchField.isEnabled()) {
            this._applyFilter();
          }
        }, this);

        this.__updateMenus();

      } else {
        this.getChildControl("search-field").setEnabled(false);
        this.getChildControl("create-menu-button").setEnabled(false);
        this.getChildControl("filter-menu-button").setEnabled(false);
      }
    },

    __reloadTree : function() {
      var selection = this.getChildControl("tree").getSelection();
      var queue = selection.length;

      selection.forEach(function(sel) {
        sel.addListenerOnce("updatedItems", function() {
          queue--;
          if (queue === 0) {
            this.__refreshTable();
          }
        }, this);
        sel.reload();
      }, this);

      // mark all other visible TreeResultItems as not loaded to trigger a reload on open
      var openNodes = this.getChildControl("tree").getOpenNodes();
      openNodes.forEach(function(node) {
        node.getChildren().forEach(function(child) {
          if (qx.lang.Array.contains(openNodes, child)) {
            // mark currently opened nodes for reload on next opening
            child.setLoaded(false);
          } else {
            child.unload();
          }
        }, this);
      }, this);
    },

    _onCreateObject : function(ev) {
      var button = ev.getTarget();

      // get currently selected dn in tree
      var selection = this.getChildControl("tree").getSelection();
      gosa.ui.controller.Objects.getInstance().openObject(selection.getItem(0).getDn(), button.getUserData("type"));
    },

    _onMoveObject : function(ev) {

      // get currently selected dn in tree
      var selection = this.getChildControl("table").getSelectionModel();

      if (selection.getSelectedCount() === 1) {
        selection.iterateSelection(function(index) {
          var row = this._tableModel.getRowData(index);
          if (qx.lang.Array.contains(this._objectRights[row[0]] || [], "w")) {
            gosa.proxy.ObjectFactory.openObject(row[3])
            .then(function(object) {
              var dialog = new gosa.ui.dialogs.actions.MoveObjectDialog(new gosa.data.controller.Actions(object));
              dialog.setAutoDispose(true);
              dialog.open();
            }, this);
          }
        }, this);
      }
    },

    _onDeleteObject : function() {
      // get currently selected dn in tree
      this.getChildControl("table").getSelectionModel().iterateSelection(function(index) {
        var row = this._tableModel.getRowData(index);
        if (qx.lang.Array.contains(this._objectRights[row[0]] || [], "d")) {
          gosa.proxy.ObjectFactory.removeObject(row[3]);
        }
      }, this);
    },

    _onOpenObject : function() {
      // get currently selected dn in tree
      var selection = this.getChildControl("table").getSelectionModel();
      if (selection.getSelectedCount() > 0) {
        this.getChildControl("spinner").show();
        var promises = [];
        selection.iterateSelection(function(index) {
          var row = this._tableModel.getRowData(index);
          if (qx.lang.Array.contains(this._objectRights[row[0]] || [], "r")) {
            promises.push(gosa.ui.controller.Objects.getInstance().openObject(row[3]));
          }
        }, this);
        qx.Promise.all(promises).finally(function() {
          this.getChildControl("spinner").exclude();
        }, this);
      }
    },

    _applyFilter : function() {
      var types = [];
      var all = 0;
      this.getChildControl("filter-menu").getChildren().forEach(function(button) {
        if (button.getValue()) {
          types.push(button.getUserData("type"));
        }
        all++;
      }, this);
      var filtered = this._tableData;

      if (types.length > 0 && types.length < all) {
        filtered = filtered.filter(function(row) {
          return qx.lang.Array.contains(types, row.type);
        });
      }
      var searchValue = this.getChildControl("search-field").getValue();
      if (searchValue && searchValue.length > 2) {
        var options = {
          shouldSort: false,
          threshold: 0.4,
          tokenize: true,
          keys: [
            "title",
            "description"
          ]
        };
        var fuse = new Fuse(filtered.toArray(), options);
        filtered = fuse.search(searchValue);
        this._tableModel.setDataAsMapArray(filtered, false, false);
      } else {
        this._tableModel.setDataAsMapArray(filtered.toArray(), false, false);
      }

    }
  },

  destruct : function() {
    this._rpc = null;

    gosa.io.Sse.getInstance().removeListener("objectRemoved", this.__debouncedReload, this);
    gosa.io.Sse.getInstance().removeListener("objectCreated", this.__debouncedReload, this);
    gosa.io.Sse.getInstance().removeListener("objectModified", this.__debouncedReload, this);
    gosa.io.Sse.getInstance().removeListener("objectMoved", this.__debouncedReload, this);

    this.__debouncedReload = null;
  }
});
