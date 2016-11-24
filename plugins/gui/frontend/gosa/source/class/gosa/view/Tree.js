/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/* ************************************************************************

#asset(gosa/*)

************************************************************************ */

qx.Class.define("gosa.view.Tree",
{
  extend : qx.ui.tabview.Page,

  construct : function(parent)
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", "@FontAwesome/sitemap");
    this.parent = parent;
    this.getChildControl("button").getChildControl("label").exclude();
    this.setLayout(new qx.ui.layout.Canvas());
    this.addListenerOnce("appear", this.load, this);
    this._rpc = gosa.io.Rpc.getInstance();

    gosa.io.Sse.getInstance().addListener("objectRemoved", this.__reloadTree, this);
    gosa.io.Sse.getInstance().addListener("objectCreated", this.__reloadTree, this);
    gosa.io.Sse.getInstance().addListener("objectModified", this.__reloadTree, this);
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

    parent : null,
    _rpc : null,
    _tableData : null,

    _createChildControlImpl : function(id, hash) {

      var control = null;

      switch(id) {

        case "tree":
          var root = new gosa.data.model.TreeResultItem(this.tr("Root"));
          root.setType("root");     // Required to show the icon
          root.load();  // Required to auto fetch children

          control = new qx.ui.tree.VirtualTree(root, "title", "children");
          control.setMinWidth(260);
          control.setSelectionMode("single");
          this.__applyTreeDelegate(control);
          this.getChildControl("splitpane").add(control, 1);
          // Act on tree selection to automatically update the list
          control.getSelection().addListener("change", this.__refreshTable, this);
          break;

        case "splitpane":
          control = new qx.ui.splitpane.Pane("horizontal");
          this.add(control, {top: 0, bottom: 0, left:0, right: 0});
          break;

        // Create the action-bar for the list panel
        case "listcontainer":
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox(5));
          control.add(this.getChildControl("toolbar"));
          this.getChildControl("splitpane").add(control, 2);
          break;

        case "toolbar":
          control = new qx.ui.toolbar.ToolBar();
          var menuPart = new qx.ui.toolbar.Part();
          var menuPart2 = new qx.ui.toolbar.Part();
          menuPart.add(this.getChildControl("action-menu-button"));
          menuPart.add(this.getChildControl("create-menu-button"));
          menuPart.add(this.getChildControl("filter-menu-button"));
          menuPart2.add(this.getChildControl("search-field"));

          control.add(menuPart2);
          control.add(menuPart);
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
          control.setMenu(this.getChildControl("action-menu"));
          break;

        case "search-field":
          control = new qx.ui.form.TextField().set({
            placeholder: this.tr("Search .."),
            liveUpdate : true
          });
          control.addListener("changeValue", this._applyFilter, this);
          break;

        case "create-menu":
          control = new qx.ui.menu.Menu();
          break;

        case "filter-menu":
          control = new qx.ui.menu.Menu();
          break;
        
        case "delete-button":
          control = new qx.ui.menu.Button(this.tr("Delete"), "@FontAwesome/trash");
          control.setEnabled(false);
          control.addListener("execute", this._onDeleteObject, this);
          break;
        
        case "action-menu":
          control = new qx.ui.menu.Menu();          
          control.add(this.getChildControl("delete-button"));
          break;

        case "table":
          // Create the table
          var tableModel = this._tableModel = new qx.ui.table.model.Simple();
          tableModel.setColumns([ "-", this.tr("Name"), this.tr("Description"), this.tr("DN"), this.tr("UUID")],
                                ['type', 'title', 'description', 'dn', 'uuid']);
          var customModel = {
            tableColumnModel : function(obj){
              return new qx.ui.table.columnmodel.Resize(obj);
            }
          };
          var table = new qx.ui.table.Table(tableModel, customModel);
          this.getChildControl("listcontainer").add(table, {flex: 1});
          table.addListener('dblclick', function(){
            table.getSelectionModel().iterateSelection(function(index) {
              this.parent.search.openObject(tableModel.getRowData(index)[3]);
            }, this);
          }, this);

          table.getSelectionModel().addListener("changeSelection", function() {
            if (table.getSelectionModel().getSelectedCount() > 0) {
              table.getSelectionModel().iterateSelection(function(index) {
                var selection = tableModel.getRowData(index);
                this.getChildControl("delete-button").setEnabled(qx.lang.Array.contains(selection[4], "d"));
              }, this);
            } else {
              this.getChildControl("delete-button").setEnabled(false);
            }
          }, this);

          table.getSelectionModel().setSelectionMode(qx.ui.table.selection.Model.SINGLE_SELECTION);
          var tcm = table.getTableColumnModel();
          var resizeBehavior = tcm.getBehavior();
          resizeBehavior.setWidth(0, 25);
          resizeBehavior.setWidth(1, "1*");
          resizeBehavior.setWidth(2, "1*");
          resizeBehavior.setWidth(3, "1*");
          tcm.setColumnVisible(3, false);
          tcm.setColumnVisible(4, false);
          tcm.setDataCellRenderer(0, new gosa.ui.table.cellrenderer.ImageByType());

          control = table;
          break;

      }

      return control || this.base(arguments, id, hash);
    },

    __applyTreeDelegate : function(tree) {
      // Special delegation handling
      var iconConverter = function(data, model) {
        if (!model.isLoading()) {
          if (model.getType()) {
            return gosa.util.Icons.getIconByType(model.getType(), 22);
          }
          return "@FontAwesome/pencil";
        } else {
          return "@FontAwesome/spinner";
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
      var tree = this.getChildControl("tree");
      tree.addListener("updatedItems", this.__refreshTable, this);
      this.getChildControl("listcontainer");
      this.getChildControl("table");
      this.__refreshTable();
    },

    __updateMenus : function() {
      var selection = this.getChildControl("tree").getSelection().getItem(0);
      if (selection) {
        // load object types
        this._rpc.cA("getAllowedSubElementsForObjectWithActions", selection.getType())
        .then(function(result) {
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
              var button = new qx.ui.menu.Button(name, icon);
              button.setAppearance("icon-menu-button");
              button.setUserData("type", name);
              this.getChildControl("create-menu").add(button);
              button.addListener("execute", this._onCreateObject, this);
            }
            if (visibleTypes[name] && allowed.includes("r")) {
              //var icon = gosa.util.Icons.getIconByType(name, 22);
              var button = new qx.ui.menu.CheckBox(name);
              //button.setAppearance("icon-menu-button");
              button.setUserData("type", name);
              this.getChildControl("filter-menu").add(button);
              button.addListener("execute", this._applyFilter, this);
            }
          }, this);
        }, this).catch(function(error) {
          new gosa.ui.dialogs.Error(error.message).open();
        });
      }
    },

    __refreshTable : function() {
      var sel = this.getChildControl("tree").getSelection();
      if (sel.length > 0) {
        this.getChildControl("create-menu-button").setEnabled(true);
        this.getChildControl("filter-menu-button").setEnabled(true);

        var done = [];
        var tableModel = this.getChildControl("table").getTableModel();
        if (!this._tableData) {
          this._tableData = new qx.data.Array();
        } else {
          this._tableData.removeAll();
        }

        var item = sel.getItem(0);
        item.load(function() {
            var children = item.getChildren().concat(item.getLeafs());
            children.forEach(function(child) {
              if(!qx.lang.Array.contains(done, child)){
                this._tableData.push(child.getTableRow());
                done.push(child);
              }
            }, this);
          tableModel.setDataAsMapArray(this._tableData.toArray());
        }, this);

        this.__updateMenus();

      } else {
        this.getChildControl("create-menu-button").setEnabled(false);
        this.getChildControl("filter-menu-button").setEnabled(false);
      }
    },

    __reloadTree : function() {
      var queue = this.getChildControl("tree").getSelection().length;
      this.getChildControl("tree").getSelection().forEach(function(sel) {
        sel.addListenerOnce("updatedItems", function() {
          queue--;
          if (queue === 0) {
            this.__refreshTable();
          }
        }, this);
        sel.reload();
      }, this);
    },

    _onCreateObject : function(ev) {
      var button = ev.getTarget();

      // get currently selected dn in tree
      var selection = this.getChildControl("tree").getSelection();
      this.parent.search.openObject(selection.getItem(0).getDn(), button.getUserData("type"));
    },

    _onDeleteObject : function() {
      // get currently selected dn in tree
      this.getChildControl("table").getSelectionModel().iterateSelection(function(index) {
        this.parent.search.removeObject(this.getChildControl("table").getTableModel().getRowData(index)[5]);
      }, this);
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
        filtered = filtered.filter(function(row) {
          return qx.lang.String.contains(row.title, searchValue);
        });
      }
      this._tableModel.setDataAsMapArray(filtered.toArray());
    }
  },

  destruct : function() {
    this._rpc = null;

    gosa.io.Sse.getInstance().removeListener("objectRemoved", this.__reloadTree, this);
    gosa.io.Sse.getInstance().removeListener("objectCreated", this.__reloadTree, this);
    gosa.io.Sse.getInstance().removeListener("objectModified", this.__reloadTree, this);
  }
});
