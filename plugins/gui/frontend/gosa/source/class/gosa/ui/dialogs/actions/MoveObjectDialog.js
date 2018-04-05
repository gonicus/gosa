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
 * Dialog for moving objects to another dn.
 */
qx.Class.define("gosa.ui.dialogs.actions.MoveObjectDialog", {
  extend: gosa.ui.dialogs.actions.Base,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct: function(actionController) {
    this.base(arguments, actionController, this.tr("Move object"));
    this._initWidgets();
  },

  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    RPC_CALLS : []
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    sourceNode: {
      check: "gosa.data.model.TreeResultItem",
      init: null,
      apply: "__openNode"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __tree: null,
    _ok: null,

    __openNode: function(node) {
      this.__tree.openNodeAndParents(node);
      this.__tree.getSelection().removeAll();
      this.__tree.getSelection().push(node);
    },

    _traverseTree: function(node, parentDn) {
      var found = false;
      if (node.getAdjustedDn() === parentDn) {
        this.setSourceNode(node);
        return true;
      }
      node.load().then(function() {
        node.getChildren().some(function(child) {
          child.load().then(function() {
            if (child.getAdjustedDn() === parentDn) {
              this.setSourceNode(child);
              found = true;
              return found;
            } else if (parentDn.endsWith(child.getAdjustedDn())) {
              child.getChildren().some(function(subChild) {
                if (parentDn.endsWith(subChild.getAdjustedDn())) {
                  return found = this._traverseTree(subChild, parentDn);
                }
              }, this)
            }
          }, this);
        }, this)
      }, this);
      return found;
    },

    _initWidgets : function() {
      var object = this._actionController.getObject();
      // create the tree
      var root = new gosa.data.model.TreeResultItem(this.tr("Root"));
      root.setMoveTarget(false);
      root.setMoveTargetFor(object.baseType);
      root.setType("root");     // Required to show the icon

      var tree = this.__tree = new qx.ui.tree.VirtualTree(root, "title", "children");
      tree.setMinHeight(600);
      tree.setHideRoot(true);
      tree.setSelectionMode("single");
      this.__applyTreeDelegate(tree);
      this.addElement(tree);
      this.__openNode(root);

      tree.getSelection().addListener("change", function() {
        var selection = tree.getSelection();
        if (selection.getLength() === 1) {
          this._ok.setEnabled(selection.getItem(0) !== this.getSourceNode());
        }
      }, this);

      object.get_adjusted_parent_dn().then(function(result) {
        this._traverseTree(root, result);
      }, this);

      var ok = gosa.ui.base.Buttons.getButton(this.tr("Move"), "@Ligature/move");
      ok.addState("default");
      ok.setEnabled(false);
      ok.setAppearance("button-primary");
      ok.addListener("execute", this._doMove, this);
      ok.setEnabled(false);
      this._ok = ok;

      var cancel = gosa.ui.base.Buttons.getCancelButton();
      cancel.addState("default");
      cancel.addListener("execute", this.close, this);

      this.addButton(ok);
      this.addButton(cancel);
    },

    /**
     * Move to the selected items DN
     */
    _doMove: function() {
      // show spinner in button
      var icon = this._ok.getChildControl("icon");
      var handle = gosa.ui.Throbber.animate(icon);
      var item = this.__tree.getSelection().getItem(0);
      this._actionController.move(item.getDn()).then(function() {
        this.close();
      }, this)
      .catch(gosa.ui.dialogs.Error.show)
      .finally(function() {
        gosa.ui.Throbber.stopAnimation(icon, handle);
      });
    },

    __applyTreeDelegate : function(tree) {
      // Special delegation handling
      var iconConverter = function(data, model) {
        if (!model.isLoading()) {
          if (model.getType()) {
            return gosa.util.Icons.getIconByType(model.getType(), 22);
          }
          return "@Ligature/pencil";
        } else {
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
          controller.bindProperty("moveTarget", "enabled", null, item, index);
          controller.bindProperty("moveTarget", "selectable", null, item, index);

          // Handle images
          controller.bindProperty("type", "icon", { converter: iconConverter }, item, index);
          controller.bindProperty("loading", "icon", { converter: iconConverter }, item, index);
        }
      };
      tree.setDelegate(delegate);
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this._disposeObjects("__tree", "_ok");
  }
});
