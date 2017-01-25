/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/* ************************************************************************

#asset(gosa/*)

************************************************************************ */

qx.Class.define("gosa.view.AbstractEditableView", {
  extend : qx.ui.tabview.Page,
  type: "abstract",
  /*
   *****************************************************************************
   CONSTRUCTOR
   *****************************************************************************
   */
  construct : function(label, icon) {
    this.base(arguments, label, icon);
    this._createChildControl("edit-mode");
    this.addListener("longtap", function() {
      this.setEditMode(true);
    }, this);
  },

  /*
   *****************************************************************************
   PROPERTIES
   *****************************************************************************
   */
  properties : {

    editMode: {
      check: "Boolean",
      init: false,
      event: "changeEditMode",
      apply: "_applyEditMode"
    },

    /**
     * Flag to determine modifications during editing mode
     */
    modified: {
      check: "Boolean",
      init: false,
      event: "changeModified"
    },

    selectedWidget: {
      check: "qx.ui.core.Widget",
      nullable: true,
      apply: "_applySelectedWidget"
    }
  },

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */
  members : {

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "header":
          control = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
          this._addAt(control, 0);
          break;

        case "toolbar":
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox(5, "center"));
          control.exclude();
          this._fillToolbar(control);
          this.getChildControl("header").add(control, {edge: 0});
          break;

        case "edit-mode":
          control = new qx.ui.form.Button(null, "@Ligature/gear/22");
          control.setZIndex(1000);
          var bounds = this.getBounds();
          if (bounds) {
            control.setUserBounds(bounds.width - 35, 0, 35, 35);
            this.add(control);
          } else {
            this.addListenerOnce("appear", function() {
              var bounds = this.getBounds();
              control.setUserBounds(bounds.width - 35, 0, 35, 35);
              this.add(control);
            }, this);
          }
          control.addListener("execute", function() {
            this.toggleEditMode();
          }, this);
          break;
      }

      return control || this.base(arguments, id);
    },

    /**
     * Can be overridden by inheriting classes to fill the toolbar acording to their needs
     * @param toolbar {qx.ui.container.Composite} "toolbar" child control
     */
    _fillToolbar: function(toolbar) {},

    // property apply
    _applyEditMode: function(value) {
      if (value) {
        this.getChildControl("toolbar").show();
      } else {
        this.getChildControl("toolbar").exclude();
        this.setSelectedWidget(null);
        this.setModified(false);
      }
    },

    // property apply
    _applySelectedWidget: function(value, old) {
      if (old) {
        old.removeState("selected");
      }
      if (value) {
        value.addState("selected");
      }
    }
  }
});
