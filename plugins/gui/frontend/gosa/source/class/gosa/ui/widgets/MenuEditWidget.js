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

    this.debouncedFireChangeValue = qx.util.Function.debounce(this.fireChangeValue.bind(this), 250);
    this.__changeListeners = {};
    this.__draw();
  },


  members : {
    __root : null,
    _type: null,
    _attribute: null,
    _editTitle: null,
    _columnNames: null,
    _columnIDs: null,
    _firstColumn: null,
    _sortByColumn: null,
    __changeListeners: null,
    _queryFilterConfig: null,
    _defaultQueryFilter: null,
    _valueQueryFilter: null,

    __draw : function() {
      this._createChildControl("toolbar");

      this.__root = new gosa.ui.tree.Folder();
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
          try {
            var roots = qx.lang.Json.parse(gosa.ui.widgets.Widget.getSingleValue(value));
            roots.forEach(function (node) {
              this.__root.add(this.__traverseJson(node));
            }, this);
          } catch (e) {
            this.error("Error parsing value: ",e);
          }
        }
      }
    },

    __traverseJson: function(node) {
      if (node.hasOwnProperty("children")) {
        qx.core.Assert.assertKeyInMap("name", node);
        var parent = this.__createItem("folder", node.name);
        parent.setOpen(true);

        node.children.forEach(function(childNode) {
          parent.add(this.__traverseJson(childNode));
        }, this);
        return parent;
      } else {
        var item = this.__createItem("app", node.name);

        Object.getOwnPropertyNames(node).forEach(function(key) {
          if (key === "gosaApplicationParameter") {
            node.gosaApplicationParameter.forEach(function(entry) {
              var parts = entry.split(":");
              item.setParameter(parts[0], parts[1]);
            });
          } else {
            if (node[key]) {
              item.set(key, node[key]);
            }
          }
        }, this);

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
      if (item instanceof gosa.ui.tree.Application) {
        res = item.toJson();
      } else if (item instanceof gosa.ui.tree.Folder) {
        res.children = [];
        item.getItems(false).forEach(function (child) {
          res.children.push(this.__traverseTree(child));
        }, this);
      }
      return res;
    },
    
    __createItem: function(type, label) {
      var item;
      switch (type) {
        case "folder":
          item = new gosa.ui.tree.Folder(label);
          break;
        case "app":
          item = new gosa.ui.tree.Application(label);
          break;
      }

      if (!this.__changeListeners.hasOwnProperty(item.toHashCode())) {
        this.__changeListeners[item.toHashCode()] = item.addListener("changedValue", this.debouncedFireChangeValue, this);
      }
      return item;
    },

    // overridden
    _createChildControlImpl : function(id) {
      var control;

      switch (id) {
        case "container":
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox());
          this.add(control, {edge: 1});
          break;

        case "split-pane":
          control = new qx.ui.splitpane.Pane();
          this.getChildControl("container").addAt(control, 1, {flex: 1});
          break;

        case "tree":
          control = new qx.ui.tree.Tree();
          control.set({
            draggable: true,
            hideRoot: true,
            selectionMode: "one"
          });
          control.addListener("changeSelection", this._onTreeSelection, this);

          this.getChildControl("split-pane").add(control, 1);
          break;

        case "form-container":
          control = new qx.ui.container.Stack();
          control.set({
            padding: [gosa.engine.processors.WidgetProcessor.CONSTANTS.CONST_SPACING_Y, gosa.engine.processors.WidgetProcessor.CONSTANTS.CONST_SPACING_X]
          });
          this.getChildControl("split-pane").add(control, 2);
          break;

        case "toolbar":
          control = new qx.ui.toolbar.ToolBar();

          var part1 = new qx.ui.toolbar.Part();
          part1.add(this.getChildControl("add-app-button"));
          part1.add(this.getChildControl("add-folder-button"));
          part1.add(new qx.ui.toolbar.Separator());
          part1.add(this.getChildControl("del-button"));
          control.add(part1);

          this.getChildControl("container").addAt(control, 0);
          break;

        case "add-app-button":
          control = new qx.ui.toolbar.Button(this.tr("Add Application"), "@Ligature/edit/22");
          control.addListener("execute", this._onAddApp, this);
          break;

        case "add-folder-button":
          control = new qx.ui.toolbar.Button(this.tr("Add Category"), "@Ligature/folder/22");
          control.addListener("execute", this._onAddFolder, this);
          break;

        case "del-button":
          control = new qx.ui.toolbar.Button(this.tr("Delete"), "@Ligature/trash/22");
          control.addListener("execute", this._onDelete, this);
          break;

      }

      return control || this.base(arguments, id);
    },

    /**
     * Handle selection changes in the tree. Show the application editing form, if an application node
     * has been selected, otherwise the name edit field for the folder.
     */
    _onTreeSelection: function() {
      var current = this.getChildControl("tree").getSelection()[0];
      if (current instanceof gosa.ui.tree.Folder) {
        // show only name field
        this._showFolderForm(current);
      } else if (current instanceof gosa.ui.tree.Application) {
        // show application menu entry form
        this._showEntryForm(current);
      }
    },

    /**
     * Show the folder edit form for the current item.
     * @param current {gosa.ui.tree.Folder}
     */
    _showFolderForm: function(current) {
      var text;
      if (!this._folderForm) {
        var form = new qx.ui.form.Form();
        text = new qx.ui.form.TextField(current.getLabel());
        text.setLiveUpdate(true);
        text.bind("value", current, "label");
        form.add(text, this.tr("Name"), null, "label");
        this._folderForm = new gosa.ui.form.renderer.Single(form, false);
        this._folderForm.getLayout().setColumnMinWidth(0, 200);
        this.getChildControl("form-container").add(this._folderForm);
      } else {
        this.getChildControl("form-container").setSelection([this._folderForm]);
        text = this._folderForm.getForm().getItems()["label"];
        text.removeAllBindings();
        text.setValue(current.getLabel());
        text.bind("value", current, "label");
      }
    },

    _showEntryForm: function(current) {
      if (this._entryForm) {
        this._entryForm.destroy();
      }
      var form = new qx.ui.form.Form();

      // name
      var text = new qx.ui.form.TextField(current.getLabel());
      text.setLiveUpdate(true);
      text.bind("value", current, "label");
      form.add(text, this.tr("Name"), null, "label");

      // get parameters from gotoApplication
      var keys = [];
      var promise = this._attribute === "dn" ?
        gosa.proxy.ObjectFactory.openObject(current.get(this._attribute)) :
        gosa.proxy.ObjectFactory.openObjectByType(this._attribute, current.get(this._attribute), this._type);

      promise.then(function(obj) {
        var parameters = obj.get("gosaApplicationParameter");
        if (parameters.length) {
          form.addGroupHeader(this.tr("Application parameters"));
          obj.get("gosaApplicationParameter").forEach(function (entry) {
            var parts = entry.split(":");
            keys.push(parts[0]);
            var field = new qx.ui.form.TextField(current.getParameterValue(parts[0]));
            field.setPlaceholder(parts[1]);
            current.initParameter(parts[0], parts[1]);
            field.setLiveUpdate(true);
            field.addListener("changeValue", function (ev) {
              current.setParameter(parts[0], ev.getData());
            }, this);
            form.add(field, parts[0], null, parts[0]);
          }, this);
          return obj.close();
        }
      }, this);

      this._entryForm = new gosa.ui.form.renderer.Single(form, false);
      this._entryForm.setHeaderAlign("center");
      this._entryForm.getLayout().setColumnMinWidth(0, 200);
      this.getChildControl("form-container").add(this._entryForm);
      this.getChildControl("form-container").setSelection([this._entryForm]);

    },

    /**
     * Adds a {@link gosa.ui.tree.Folder} to the tree.
     */
    _onAddFolder: function() {
      // Ask user for name
      var d = new gosa.ui.dialogs.PromptTextDialog(this.tr("Enter name"), null, this.tr("Name"));
      d.addListenerOnce("ok", function(ev) {
        var node = this.__createItem("folder", ev.getData());
        this.insertNewNode(node);
        this.fireChangeValue();
      }, this);
      d.open();
    },

    /**
     * Adds a {@link gosa.ui.tree.Application}, which represents an application, to the tree.
     */
    _onAddApp: function() {
      var options = {};
      if (this._queryFilterConfig) {
        if (this._queryFilterConfig.valueFrom) {
          // get value from current objects attribute
          var object = this._getController().getObject();
          var value = gosa.ui.widgets.Widget.getSingleValue(object.get(this._queryFilterConfig.valueFrom));
          if (value) {
            options.queryFilter = this._valueQueryFilter.replace("###VAL###", value);
          }
        }
        if (!options.queryFilter && this._defaultQueryFilter) {
          // use default filter
          options.queryFilter = this._defaultQueryFilter;
        }
      }
      var d = new gosa.ui.dialogs.ItemSelector(
        this['tr'](this._editTitle),
        [],
        this._type,
        this._attribute,
        {
          ids: this._columnIDs,
          names: this._columnNames
        },
        false,
        null,
        this._sortByColumn,
        "searchObjects",
        options
      );

      d.addListener("selected", function(e){
        var data = e.getData();
        if (data.length) {

          data.forEach(function(entry) {
            var node = this.__createItem("app", entry[this._firstColumn]);
            delete entry["__identifier__"];
            node.set(entry);
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
      var current = this.getChildControl("tree").getSelection()[0];
      if (!current) {
        // append to root node
        this.__root.add(node);
        this.__root.setOpen(true);
      } else if (node instanceof gosa.ui.tree.Folder) {
        // folders only on root level -> always add after current
        while (current instanceof gosa.ui.tree.Application) {
          current = current.getParent();
        }
        current.getParent().addAfter(node, current);
      } else {
        // add application
        if (current instanceof gosa.ui.tree.Folder) {
          // insert
          current.add(node);
          current.setOpen(true);
        } else {
          // append
          current.getParent().addAfter(node, current);
        }
      }
      // select the new node
      var selection = this.getChildControl("tree").getSelection();
      if (selection.length) {
        selection[0] = node;
      } else {
        selection.push(node)
      }
    },

    _onDelete: function() {
      var current = this.getChildControl("tree").getSelection()[0];
      if (current && current !== this.__root) {
        // delete all listeners
        current.getItems().forEach(function(item) {
          if (this.__changeListeners.hasOwnProperty(item.toHashCode())) {
            item.removeListenerById(this.__changeListeners[item.toHashCode()]);
          }
        }, this);
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
      }

      if (props.hasOwnProperty("editTitle")) {
        this._editTitle = props.editTitle;
      }

      if (props.hasOwnProperty("queryFilter")) {
        this._queryFilterConfig = props.queryFilter;
        this._defaultQueryFilter = props.queryFilter.base+","+gosa.Session.getInstance().getBase();
        if (props.queryFilter.hasOwnProperty("valueFrom") && props.queryFilter.hasOwnProperty("valueRDN")) {
          this._valueQueryFilter = props.queryFilter.valueRDN+"=###VAL###,"+this._defaultQueryFilter;
        }
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
