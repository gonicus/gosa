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

  members : {
    /**
     * @type {gosa.data.controller.Workflow | null}
     */
    __controller : null,

    setController : function(controllerObject) {
      this.__controller = controllerObject;
      this.__fillSideBar(this.__controller.getSideBarData());
    },

    /**
     * @param stepIndex {Integer} First step is 0 (so must be an integer >= 0)
     */
    showStep : function(stepIndex) {
      var stack = this.getChildControl("stack");

      if (!stack[stepIndex]) {
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

    // overridden
    _createChildControlImpl : function(id) {
      var control;

      switch (id) {
        case "sidebar":
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox());
          this.add(control);
          break;

        case "stack":
          control = new qx.ui.container.Stack();
          this.add(control);
          break;
      }

      return control || this.base(arguments, id);
    }
  },

  destruct : function() {
    this.__controller = null;
  }
});
