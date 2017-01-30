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
    // do not store these properties in the backend
    // please not that these string are treated as wildcards e.g. matching resizable*
    this.__doNotStoreProps = ["resizable", "droppable"];
    this.addListener("dragover", this._onDragOver, this);
    this.__options = gosa.data.DashboardController.getWidgetOptions(this);

    if (this.__options.maxRowspan) {
      this.setMaxRowSpan(parseInt(this.__options.maxRowspan));
    }
    if (this.__options.maxColspan) {
      this.setMaxColSpan(parseInt(this.__options.maxColspan));
    }
    if (this.__options.minRowspan) {
      this.setMinRowSpan(parseInt(this.__options.minRowspan));
    }
    if (this.__options.minColspan) {
      this.setMinColSpan(parseInt(this.__options.minColspan));
    }
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
    },

    title: {
      check: "String",
      nullable: true,
      apply: "_applyTitle"
    },
  },
    
  members : {
    __options: null,
    __doNotStoreProps: null,

    // overidden
    /**
     * @lint ignoreReferenceField(_forwardStates)
     */
    _forwardStates : {
      disabled : true,
      pressed : true,
      edit : true,
      hovered : true
    },

    isEditable: function() {
      return !!this.__options.settings;
    },

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "container":
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox());
          control.setAnonymous(true);
          this._add(control, { edge: 0 });
          break;

        case "title":
          control = new qx.ui.basic.Label();
          this.getChildControl("container").addAt(control, 0);
          break;

        case "content":
          control = new qx.ui.container.Composite(new qx.ui.layout.Grow());
          control.setAllowGrowX(true);
          this.getChildControl("container").addAt(control, 1, {flex: 1});
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
        if (this.__options.hasOwnProperty("resizable")) {
          this.setResizable(this.__options.resizable);
        } else {
          this.setResizable(true);
        }
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
          if (this.__doNotStoreProps.indexOf(name) !== -1) {
            return;
          }
          if (!!this.__doNotStoreProps.find(function(item) {
            return name.startsWith(item);
          }, this)) {
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