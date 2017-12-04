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
 * A widget that allows to select the base for an object.
 */
qx.Class.define("gosa.ui.widgets.QBaseSelectorWidget", {

  extend : gosa.ui.widgets.Widget,

  construct : function() {
    this.base(arguments);
    this.__draw();
  },

  properties : {
    appearance: {
      refine: true,
      init: "base-selector"
    },

    /**
     * The type of the object for which a base shall be selected, e.g. "user".
     */
    objectType : {
      check : "Array",
      init : null,
      event : "changeObjectType",
      apply : "__generateTreeDelegate"
    }
  },

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events: {
    "changeObjectType": "qx.event.type.Data"
  },

  members : {
    __root : null,
    __objectTypes: null,

    setObjectTypes: function(values) {
      var old = this.__objectTypes ? this.__objectTypes.slice(0) : null;
      this.__objectTypes = values;
      this.fireDataEvent("changeObjectType", this.__objectTypes, old);
    },

    setObjectType: function(value) {
      var old = this.__objectTypes ? this.__objectTypes.slice(0) : null;
      if (value) {
        if (!this.__objectTypes) {
          this.__objectTypes = [value];
          this.fireDataEvent("changeObjectType", this.__objectTypes, null);
        } else if (!this.__objectTypes.includes(value)) {
          this.__objectTypes.push(value);
        }
      } else {
        // resetting value
        this.__objectTypes = null;
      }
      this.fireDataEvent("changeObjectType", this.__objectTypes, old);
    },

    getObjectType: function() {
      return this.__objectTypes;
    },

    __draw : function() {
      this.__root = new gosa.data.model.TreeResultItem(this.tr("Root"));
      this.__root.setMoveTarget(false);
      this.__root.setMoveTargetFor(this.__objectTypes);
      this.addListener("changeObjectType", function(ev) {
        this.__root.setMoveTargetFor(ev.getData());
      }, this);
      this.__root.setType("root");  // Required to show the icon
      this.__root.load().then(function() {
        var firstChild = this.__root.getChildren().getItem(0);
        this.getChildControl("tree").openNode(firstChild);
        firstChild.load();
      }, this);
    },

    __generateTreeDelegate : function() {
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

      this.getChildControl("tree").setDelegate(delegate);
    },

    __onSelectionChange : function() {
      var atomicValue = this.getChildControl("tree").getSelection().getItem(0).getDn();
      this.setValue(new qx.data.Array([atomicValue]));
      this.__validate();
      this.fireDataEvent("changeValue", this.getValue());
    },

    __validate : function() {
      this.setValid(!this.isMandatory() || this.getValue().getLength() > 0);
    },

    // overridden
    _createChildControlImpl : function(id) {
      var control;

      switch (id) {
        case "tree":
          control = new qx.ui.tree.VirtualTree(this.__root, "title", "children");
          control.setWidth(null);
          control.getChildControl("pane").setWidth(null);
          control.setHideRoot(true);
          control.setSelectionMode("one");

          control.getSelection().addListener("change", this.__onSelectionChange, this);

          this.add(control, {edge : 0});
          break;
      }

      return control || this.base(arguments, id);
    }
  },

  destruct : function() {
    this._disposeObjects("__root");
  }
});
