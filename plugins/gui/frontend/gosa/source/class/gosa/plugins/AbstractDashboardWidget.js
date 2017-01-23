/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* Base class for all dashboard widgets
*/
qx.Class.define("gosa.plugins.AbstractDashboardWidget", {
  extend : qx.ui.core.Widget,
  implement: gosa.plugins.IPlugin,
  type: "abstract",
  include: gosa.ui.core.MGridResizable,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function() {
    this.base(arguments);
    this._setLayout(new qx.ui.layout.Canvas());
    this.set({
      resizable: false
    });
    this.setDroppable(true);
    this.addListener("dragover", this._onDragOver, this);
  },

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events : {
    "delete": "qx.event.type.Event"
  },
    
  properties : {
    appearance: {
      refine: true,
      init: "gosa-dashboard-widget"
    },

    editMode: {
      check: "Boolean",
      init: false,
      apply: "_applyEditMode"
    }
  },
    
  members : {
    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "container":
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox());
          this._add(control, { edge: 0 });
          break;

        case "title":
          control = new qx.ui.basic.Label();
          this.getChildControl("container").add(control);
          break;

        case "content":
          control = new qx.ui.container.Composite(new qx.ui.layout.Grow());
          this.getChildControl("container").add(control, {flex: 1});
          break;

      }

      return control || this.base(arguments, id);
    },

    // property apply
    _applyEditMode: function(value) {
      this.setDraggable(value);
      this.getChildControl("container").setEnabled(!value);
      if (value) {
        this.addListener("dragstart", this.__onDragStart, this);
        this.addState("edit");
        this.setResizable(true);
      } else {
        this.removeListener("dragstart", this.__onDragStart, this);
        this.removeState("edit");
        this.setResizable(false);
      }
    },

    __onDragStart: function(e) {
      e.addAction("move");
    },

    _onDragOver: function(e) {
      gosa.ui.core.GridCellDropbox.setStartBuddy(null);
      e.preventDefault();
    },

    // property apply
    _applyTitle: function(value) {
      var control = this.getChildControl("title");
      if (value) {
        control.setValue(value);
        control.show();
      } else {
        control.exclude();
      }
    },

    // can be overridden by subclasses for more sophisticated configurations
    configure: function(properties) {
      this.set(properties);
    },

    /**
     * Return the user defined properties as Map
     * @return {Map}
     */
    getConfiguration: function() {
      var config = {};
      Object.getOwnPropertyNames(this).forEach(function(prop) {
        if (prop.substring(0, 7) === "$$user_") {
          var name = prop.substring(7);
          if (name.startsWith("resizable")) {
            return;
          }
          // user defined property value found, check if it is != its init value
          if (qx.util.PropertyUtil.getInitValue(this, name) !== this[prop]) {
            config[name] = this[prop];
          }
        }
      }, this);
      return config;
    }
  }
});