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
 * A widget that allows to define and modify a tree of menu entries.
 */
qx.Class.define("gosa.ui.widgets.MenuEditWidget", {

  extend : gosa.ui.widgets.Widget,

  construct : function() {
    this.base(arguments);
    this.__draw();
    this.__userDataKeys = [];
  },


  members : {
    __userDataKeys: [],
    __root : null,
    _type: null,
    _attribute: null,
    _editTitle: null,
    _columnNames: null,
    _columnIDs: null,
    _firstColumn: null,
    _sortByColumn: null,

    __draw : function() {
      this._createChildControl("toolbar");

      this.__root = new qx.ui.tree.TreeFolder();
      this.__root.setOpen(true);
      var tree = this.getChildControl("tree");
      tree.setRoot(this.__root);

      this._applyValue(this.getValue());
    },

    _applyValue: function(value) {
      if (this.__root) {
        this.__root.removeAll();
        if (value && value.length) {
          // create tree from json
          var roots = qx.lang.Json.parse(gosa.ui.widgets.Widget.getSingleValue(value));
          roots.forEach(function(node) {
            this.__root.add(this.__traverseJson(node));
          }, this);
        }
      }
    },

    __traverseJson: function(node) {
      if (node.hasOwnProperty("children")) {
        qx.core.Assert.assertKeyInMap("name", node);
        var parent = new qx.ui.tree.TreeFolder(node.name);
        parent.setOpen(true);

        node.children.forEach(function(childNode) {
          parent.add(this.__traverseJson(childNode));
        }, this);
        return parent;
      } else {
        var item = new qx.ui.tree.TreeFile(node.name);

        this.__userDataKeys.forEach(function(key) {
          qx.core.Assert.assertKeyInMap(key, node);
          item.setUserData(key, node[key]);
        });

        return item;
      }
    },

    /**
     * Create Json from current tree
     * @private
     */
    __serialize: function() {
      var res = [];
      this.__root.getItems(false).forEach(function(child) {
        res.push(this.__traverseTree(child));
      }, this);
      return res;
    },

    __traverseTree: function(item) {
      var res = {name: item.getLabel()};
      if (item instanceof qx.ui.tree.TreeFile) {
        this.__userDataKeys.forEach(function (key) {
          if (item.getUserData(key)) {
            res[key] = item.getUserData(key);
          }
        });
      } else if (item instanceof qx.ui.tree.TreeFolder) {
        res.children = [];
        item.getItems(false).forEach(function (child) {
          res.children.push(this.__traverseTree(child));
        }, this);
      }
      return res;
    },

    // overridden
    _createChildControlImpl : function(id) {
      var control;

      switch (id) {
        case "container":
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox());
          this.add(control, {edge: 1});
          break;

        case "tree-container":
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox());
          this.getChildControl("container").add(control);
          break;

        case "tree":
          control = new qx.ui.tree.Tree();
          control.set({
            draggable: true,
            hideRoot: true,
            selectionMode: "one"
          });

          this.getChildControl("tree-container").addAt(control, 1, {flex: 1});
          break;

        case "form":
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox());
          this.getChildControl("container").add(control, {flex: 1});
          break;

        case "toolbar":
          control = new qx.ui.toolbar.ToolBar();

          var part1 = new qx.ui.toolbar.Part();
          part1.add(this.getChildControl("add-app-button"));
          part1.add(this.getChildControl("add-folder-button"));
          part1.add(new qx.ui.toolbar.Separator());
          part1.add(this.getChildControl("del-button"));
          control.add(part1);

          this.getChildControl("tree-container").addAt(control, 0);
          break;

        case "add-app-button":
          control = new qx.ui.toolbar.Button(this.tr("Add Application"), "@Ligature/edit/22");
          control.addListener("execute", this._onAddApp, this);
          break;

        case "add-folder-button":
          control = new qx.ui.toolbar.Button(this.tr("Add Folder"), "@Ligature/folder/22");
          control.addListener("execute", this._onAddFolder, this);
          break;

        case "del-button":
          control = new qx.ui.toolbar.Button(this.tr("Delete"), "@Ligature/trash/22");
          control.addListener("execute", this._onDelete, this);
          break;

      }

      return control || this.base(arguments, id);
    },

    _onAddFolder: function() {
      // Ask user for name
      var d = new gosa.ui.dialogs.PromptTextDialog(this.tr("Enter name"), null, this.tr("Name"));
      d.addListener("ok", function(ev) {
        var node = new qx.ui.tree.TreeFolder(ev.getData());
        this.insertNewNode(node);
        this.fireChangeValue();
      }, this);
      d.open();
    },

    _onAddApp: function() {
      var d = new gosa.ui.dialogs.ItemSelector(
        this['tr'](this._editTitle),
        [],
        this._type,
        this._attribute,
        this._columnIDs,
        this._columnNames,
        false,
        null,
        this._sortByColumn,
        "searchObjects"
      );

      d.addListener("selected", function(e){
        var data = e.getData();
        if (data.length) {

          data.forEach(function(entry) {
            var node = new qx.ui.tree.TreeFile(entry[this._firstColumn]);
            node.setUserData(this._attribute, entry[this._attribute]);
            this.insertNewNode(node);
          }, this);

          this.fireChangeValue();
        }
      }, this);

      d.open();
    },

    fireChangeValue: function() {
      var value = this.getValue().copy();
      value.setItem(0, qx.lang.Json.stringify(this.__serialize()));
      this.fireDataEvent("changeValue", value);
    },

    insertNewNode: function(node) {
      // add to tree after currently selected item
      var current = this.getChildControl("tree").getSelection()[0] || this.__root;
      if (current instanceof qx.ui.tree.TreeFile) {
        // after
        current.getParent().addAfter(node, current);
      } else if (current instanceof qx.ui.tree.TreeFolder) {
        // inside
        current.add(node);
        current.setOpen(true);
      }
    },

    _onDelete: function() {
      var current = this.getChildControl("tree").getSelection()[0];
      if (current && current !== this.__root) {
        current.getParent().remove(current);
        this.fireChangeValue();
      }
    },

    _applyGuiProperties: function(props){

      // This happens when this widgets gets destroyed - all properties will be set to null.
      if(props === null){
        return;
      }

      if (props.hasOwnProperty("type")) {
        this._type = props.type;
      }

      if (props.hasOwnProperty("attribute")) {
        this._attribute = props.attribute;
        this.__userDataKeys.push(props.attribute);
      }

      if (props.hasOwnProperty("editTitle")) {
        this._editTitle = props.editTitle;
      }

      this._columnNames = [];
      this._columnIDs = [];
      var first = null;
      if('columns' in props){
        for(var col in props['columns']){
          if (props['columns'].hasOwnProperty(col)) {
            this._columnNames.push(this['tr'](props['columns'][col]));
            this._columnIDs.push(col);
            if (!first) {
              first = col;
            }
          }
        }
      }
      this._firstColumn = first;
      if ("sortByColumn" in props) {
        this._sortByColumn = props.sortByColumn;
      }
    }
  },

  destruct : function() {
    this._disposeObjects("__root");
  }
});
