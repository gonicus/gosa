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
    this.base(arguments, "", gosa.Config.getImagePath("apps/tree.png", 32));
    this.parent = parent;
    this.getChildControl("button").getChildControl("label").exclude();
    this.setLayout(new qx.ui.layout.Canvas());
    this.addListenerOnce("appear", this.load, this);
  },

  members : {

    parent : null,
    splitpane : null,

    load : function(){
      this.splitpane = new qx.ui.splitpane.Pane("horizontal");
      this.add(this.splitpane, {top: 0, bottom: 0, left:0, right: 0});

      //var tree = new qx.ui.treevirtual.TreeVirtual("Tree");
      var root = new gosa.data.model.TreeResultItem(this.tr("Root"));
      root.setType("root");     // Required to show the icon
      root.load();  // Required to auto fetch children

      // Create the Tree
      var tree = new qx.ui.tree.VirtualTree(root, "title", "children");
      tree.setMinWidth(260);
      tree.setSelectionMode("multi");

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
            if (!item.isLoading()){
              if(item.getType()){
                var path = gosa.Config.spath + "/resources/images/objects/22/" + item.getType().toLowerCase() + ".png";
                path = document.URL.replace(/\/[^\/]*[a-zA-Z]\/.*/, "") + path;
                return path;
              }
              return(gosa.Config.getImagePath("actions/document-edit.png", 22));
            } else {
              return(gosa.Config.getImagePath("status/loading.gif", 22));
            }
          }}, item, index);
        }
      };
      tree.setDelegate(delegate);

      this.splitpane.add(tree, 1);

      // Create the action-bar for the list panel
      var listContainer = new qx.ui.container.Composite(new qx.ui.layout.VBox(5));
      var toolbar = new qx.ui.toolbar.ToolBar;
      var menuPart = new qx.ui.toolbar.Part;
      var menuPart2 = new qx.ui.toolbar.Part;
      var actionMenu = new qx.ui.toolbar.MenuButton("Action");
      var createMenu = new qx.ui.toolbar.MenuButton("Create");
      var filterMenu = new qx.ui.toolbar.MenuButton("Show");
      menuPart.add(actionMenu);
      menuPart.add(createMenu);
      menuPart.add(filterMenu);
      menuPart2.add(new qx.ui.form.TextField().set({placeholder: this.tr("Search ..")}).set({enabled: false}));
      toolbar.add(menuPart2);
      toolbar.add(menuPart);

      //TODO: enable some time
      toolbar.setEnabled(false);

      listContainer.add(toolbar);
      this.splitpane.add(listContainer, 2);

      // Create the table
      var tableModel = this._tableModel = new qx.ui.table.model.Simple();
      tableModel.setColumns([ "-", this.tr("Name"), this.tr("Description"), this.tr("DN"), this.tr("Actions")]);
      var customModel = {
        tableColumnModel : function(obj){
          return new qx.ui.table.columnmodel.Resize(obj);
        }
      }
      var table = new qx.ui.table.Table(tableModel, customModel);
      listContainer.add(table, {flex: 1});
      var that = this;
      table.addListener('dblclick', function(){
          table.getSelectionModel().iterateSelection(function(index) {
              that.parent.search.openObject(tableModel.getRowData(index)[3]);
          });
        }, this);


      var ImageByType = qx.Class.define("ImageByType",{
        extend : qx.ui.table.cellrenderer.Image,
        members :      {
          _getImageInfos : function(cellInfo){
            var path = gosa.Config.spath + "/resources/images/objects/16/" + cellInfo['value'].toLowerCase() + ".png";
            path = document.URL.replace(/\/[^\/]*[a-zA-Z]\/.*/, "") + path;
            cellInfo['value'] = path;
            return(this.base(arguments, cellInfo));
          }
        }
      });

      var Action = qx.Class.define("Action",{
        extend : qx.ui.table.cellrenderer.Boolean,
        members :      {
          _getImageInfos : function(cellInfo){
            cellInfo['value'] =  gosa.Config.spath + "/resources/images/objects/16/" + cellInfo['value'].toLowerCase() + ".png";
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
      tcm.setDataCellRenderer(0, new ImageByType());

      // Act on tree selection to automatically update the list
      tree.getSelection().addListener("change", function(e){
        var sel = tree.getSelection();
        var data = [];
        var done = [];
        tableModel.setData([]);
        var f = function(item){
          if(!qx.lang.Array.contains(done, item)){
            tableModel.addRows([item.getTableRow()]);
            done.push(item);
          }
        }

        var f2 = function(index){
          sel.getItem(index).load(function(){
            if(sel.getItem(index).getChildren()){
              for(var j=0; j<sel.getItem(index).getChildren().getLength(); j++){
                f(sel.getItem(index).getChildren().getItem(j));
              }
            }
            if(sel.getItem(index).getLeafs()){
              for(var j=0; j<sel.getItem(index).getLeafs().getLength(); j++){
                f(sel.getItem(index).getLeafs().getItem(j));
              }
            }
          },this);
        } 
        for(var i=0; i<sel.getLength(); i++){
          f2(i);
        }
      }, this);
    }
  }
});
