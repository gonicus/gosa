/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Container showing several tabs - all necessary for displaying forms for editing an object.
 */
qx.Class.define("gosa.ui.widgets.WorkflowWizard", {

  extend: qx.ui.container.Composite,

  construct: function() {
    this.base(arguments);
    this.setLayout(new qx.ui.layout.HBox());
  },

  events : {
    "close" : "qx.event.type.Event"
  },

  properties : {

    /**
     * Show the save button in favor of the next button.
     */
    showSaveButton : {
      check : "Boolean",
      init : false,
      apply : "_applyShowSaveButton"
    }
  },

  members : {
    /**
     * @type {gosa.data.controller.Workflow | null}
     */
    __controller : null,

    setController : function(controllerObject) {
      this.__controller = controllerObject;
      this.__fillSideBar(this.__controller.getSideBarData());
      this.__createButtons();
    },

    close : function() {
      this.fireEvent("close");
      this.destroy();
    },

    /**
     * @param stepIndex {Integer} First step is 0 (so must be an integer >= 0)
     */
    showStep : function(stepIndex) {
      var stack = this.getChildControl("stack");

      if (!stack.getChildren()[stepIndex]) {
        this.__createStepWidget(stepIndex);
      }
      stack.setSelection([stack.getChildren()[stepIndex]]);
    },

    /**
     * @param stepIndex {Integer}
     */
    __createStepWidget : function(stepIndex) {
      qx.core.Assert.assertUndefined(this.getChildControl("stack").getChildren()[stepIndex]);

      var container = this.__createNewStepContainer();
      this.__controller.createContextForIndex(stepIndex, container);
      this.getChildControl("stack").addAt(container, stepIndex);
    },

    __createNewStepContainer : function() {
      return new qx.ui.container.Composite(new qx.ui.layout.VBox());
    },

    /**
     * @param sideBarData {Array}
     */
    __fillSideBar : function(sideBarData) {
      sideBarData.forEach(function(item, index) {
        this.__createSideBarItem(index, item.name, item.description);
      }, this);
    },

    /**
     * @param index {Integer}
     * @param name {String}
     * @param description {String ? undefined}
     */
    __createSideBarItem : function(index, name, description) {
      var label = new qx.ui.basic.Label("<strong>" + (index + 1) + ". " + name + "</strong>");
      label.setRich(true);
      this.getChildControl("sidebar").add(label);

      if (description) {
        label = new qx.ui.basic.Label(description);
        this.getChildControl("sidebar").add(label);
      }
    },

    _applyShowSaveButton : function(value) {
      this.getChildControl("save-button").setVisibility(value ? "visible" : "excluded");
      this.getChildControl("next-button").setVisibility(value ? "excluded" : "visible");
    },

    __createButtons : function() {
      this.getChildControl("cancel-button");
      this.getChildControl("previous-button");
      this.getChildControl("next-button");
    },

    // overridden
    _createChildControlImpl : function(id) {
      var control;

      switch (id) {
        case "form-container":
          var layout = new qx.ui.layout.VBox();
          layout.setAlignX("right");
          control = new qx.ui.container.Composite(layout);
          this.add(control);
          break;

        case "sidebar":
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox());
          this.add(control);
          break;

        case "stack":
          control = new qx.ui.container.Stack();
          this.getChildControl("form-container").addAt(control, 0);
          break;

        case "button-group":
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox());
          this.getChildControl("form-container").addAt(control, 1);
          break;

        case "cancel-button":
          control = new qx.ui.form.Button(this.tr("Cancel"));
          control.addListener("execute", this.__controller.close, this.__controller);
          this.getChildControl("button-group").add(control);
          break;

        case "next-button":
          control = new qx.ui.form.Button(this.tr("Next"));
          control.addListener("execute", this.__controller.nextStep, this.__controller);
          this.getChildControl("button-group").add(control);
          break;

        case "previous-button":
          control = new qx.ui.form.Button(this.tr("Previous"));
          control.addListener("execute", this.__controller.previousStep, this.__controller);
          this.getChildControl("button-group").add(control);
          break;

        case "save-button":
          control = new qx.ui.form.Button(this.tr("Save & Close"));
          control.addListener("execute", this.__controller.saveAndClose, this.__controller);
          this.getChildControl("button-group").add(control);
          break;
      }

      return control || this.base(arguments, id);
    }
  },

  destruct : function() {
    this.__controller = null;
  }
});
