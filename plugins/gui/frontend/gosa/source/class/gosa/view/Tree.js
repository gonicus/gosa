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

  members : {

    parent : null,
    _deleteButton : null,
    _rpc : null,

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
          console.log("adding and creating splitpane");
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
          control = new qx.ui.toolbar.ToolBar;
          var menuPart = new qx.ui.toolbar.Part;
          var menuPart2 = new qx.ui.toolbar.Part;
          var actionMenuButton = new qx.ui.toolbar.MenuButton("Action");
          var createMenuButton = this._createMenuButton = new qx.ui.toolbar.MenuButton("Create");
          var filterMenuButton = new qx.ui.toolbar.MenuButton("Show");
          menuPart.add(actionMenuButton);
          menuPart.add(createMenuButton);
          menuPart.add(filterMenuButton);
          menuPart2.add(new qx.ui.form.TextField().set({placeholder: this.tr("Search ..")}).set({enabled: false}));
          control.add(menuPart2);
          control.add(menuPart);

          var actionMenu = new qx.ui.menu.Menu();
          actionMenuButton.setMenu(actionMenu);
          var deleteButton = this._deleteButton = new qx.ui.menu.Button(this.tr("Delete"), "@FontAwesome/trash");
          deleteButton.setAppearance("icon-menu-button");
          actionMenu.add(deleteButton);
          deleteButton.setEnabled(false);

          deleteButton.addListener("execute", this._onDeleteObject, this);

          var createMenu = this.getChildControl("createMenu");
          createMenuButton.setMenu(createMenu);
          break;

        case "createMenu":
          control = new qx.ui.menu.Menu();
          break;

        case "table":
          // Create the table
          var tableModel = this._tableModel = new qx.ui.table.model.Simple();
          tableModel.setColumns([ "-", this.tr("Name"), this.tr("Description"), this.tr("DN"), this.tr("Actions"), this.tr("UUID")]);
          var customModel = {
            tableColumnModel : function(obj){
              return new qx.ui.table.columnmodel.Resize(obj);
            }
          };
          var table = new qx.ui.table.Table(tableModel, customModel);
          this.getChildControl("listcontainer").add(table, {flex: 1});
          var that = this;
          table.addListener('dblclick', function(){
            table.getSelectionModel().iterateSelection(function(index) {
              that.parent.search.openObject(tableModel.getRowData(index)[3]);
            });
          }, this);

          table.getSelectionModel().addListener("changeSelection", function() {
            // TODO: check if the selected object is deletable, check ACL too?
            this._deleteButton.setEnabled(table.getSelectionModel().getSelectedCount() > 0);
          }, this);

          var Action = qx.Class.define("Action",{
            extend : qx.ui.table.cellrenderer.Boolean,
            members :      {
              _getImageInfos : function(cellInfo){
                cellInfo['value'] =  gosa.Config.spath + "/" + gosa.Config.getTheme() + "/resources/images/objects/16/" + cellInfo['value'].toLowerCase() + ".png";
                return(this.base(arguments, cellInfo));
              }
            }
          });


          table.getSelectionModel().setSelectionMode(qx.ui.table.selection.Model.SINGLE_SELECTION);
          var tcm = table.getTableColumnModel();
          var resizeBehavior = tcm.getBehavior();
          resizeBehavior.setWidth(0, 25);
          resizeBehavior.setWidth(1, "1*");
          resizeBehavior.setWidth(2, "1*");
          resizeBehavior.setWidth(3, "1*");
          tcm.setColumnVisible(3, false);
          tcm.setColumnVisible(5, false);
          tcm.setDataCellRenderer(0, new gosa.ui.table.cellrenderer.ImageByType());

          control = table;
          break;

      }

      return control || this.base(arguments, id, hash);
    },

    __applyTreeDelegate : function(tree) {
      // Special delegation handling
      var delegate = {

        // Bind properties from the item to the tree-widget and vice versa
        bindItem : function(controller, item, index){
          controller.bindDefaultProperties(item, index);
          controller.bindPropertyReverse("open", "open", null, item, index);
          controller.bindProperty("open", "open", null, item, index);
          controller.bindProperty("dn", "toolTipText", null, item, index);

          // Handle images
          controller.bindProperty("", "icon", {converter: function(item){
            if (!item.isLoading()) {
              if(item.getType()) {
                return gosa.util.Icons.getIconByType(item.getType(), 22);
              }
              return "@FontAwesome/pencil";
            } else {
              return "@FontAwesome/spinner";
            }
          }}, item, index);
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
      //this.__updateCreateMenu();
      this.__refreshTable();
    },

    __updateCreateMenu : function() {
      var selection = this.getChildControl("tree").getSelection().getItem(0);
      if (selection) {
        // load object types
        this._rpc.cA(function(result, error) {
          if (error) {
            new gosa.ui.dialogs.Error(error.message).open();
          }
          else {
            result.sort();
            this.getChildControl("createMenu").removeAll();
            for (var index in result) {
              var name = result[index];
              var icon = gosa.util.Icons.getIconByType(name, 22);
              var button = new qx.ui.menu.Button(name, icon);
              button.setAppearance("icon-menu-button");
              button.setUserData("type", name);
              this.getChildControl("createMenu").add(button);
              button.addListener("execute", this._onCreateObject, this);
            }
          }
        }, this, "getAllowedSubElementsForObject", selection.getType());
      }
    },

    __refreshTable : function() {
      var sel = this.getChildControl("tree").getSelection();
      this._createMenuButton.setEnabled(sel.length > 0);

      var done = [];
      var tableModel = this.getChildControl("table").getTableModel();
      tableModel.setData([]);
      var f = function(item){
        if(!qx.lang.Array.contains(done, item)){
          tableModel.addRows([item.getTableRow()]);
          done.push(item);
        }
      };

      var f2 = function(index){
        sel.getItem(index).load(function(){
          if(sel.getItem(index).getChildren()){
            sel.getItem(index).getChildren().forEach(f);
          }
          if(sel.getItem(index).getLeafs()){
            sel.getItem(index).getLeafs().forEach(f);
          }
        },this);
      };
      for(var i=0; i<sel.getLength(); i++){
        f2(i);
      }
      if (sel.length > 0) {
        this.__updateCreateMenu();
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
    }
  },

  destruct : function() {
    this._rpc = null;
    this._disposeObjects("_deleteButton", "_createMenuButton");

    gosa.io.Sse.getInstance().removeListener("objectRemoved", this.__reloadTree, this);
    gosa.io.Sse.getInstance().removeListener("objectCreated", this.__reloadTree, this);
    gosa.io.Sse.getInstance().removeListener("objectModified", this.__reloadTree, this);
  }
});
