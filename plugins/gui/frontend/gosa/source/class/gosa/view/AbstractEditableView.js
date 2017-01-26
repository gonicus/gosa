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
    this.addListener("longtap", function() {
      this.setEditMode(true);
    }, this);

    this.addListener("resize", this._onResize, this);
    this.addListener("appear", this._onResize, this);
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

    _onResize : function() {
      var bounds = this.getBounds();
      var editControl = this.getChildControl("edit-mode");
      if (bounds) {
        editControl.setUserBounds(bounds.width - 28, 0, 28, 28);
      }
    },

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
          control.addListener("execute", function() {
            if (this.isModified() && this.isEditMode()) {
              // get user confirmation to skip changes
              var dialog = new gosa.ui.dialogs.Confirmation(this.tr("Unsaved changes"), this.tr("Do you want to discard those changes?"), "warning");
              dialog.addListenerOnce("confirmed", function(ev) {
                if (ev.getData() === true) {
                  this.setEditMode(false);
                  this.refresh();
                }
              }, this);
              dialog.open();
            } else {
              if (this.isEditMode()) {
                this.refresh();
              }
              this.toggleEditMode();
            }
          }, this);

          this.add(control);
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
        this.getChildControl("edit-mode").exclude();
      } else {
        this.getChildControl("toolbar").exclude();
        this.getChildControl("edit-mode").show();
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
