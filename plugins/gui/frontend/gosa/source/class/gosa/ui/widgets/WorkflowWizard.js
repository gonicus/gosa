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
      this.getChildControl("sidebar");
    },

    /**
     * @param stepIndex {Integer} First step is 0 (so must be an integer >= 0)
     */
    showStep : function(stepIndex) {
      qx.core.Assert.assertPositiveInteger(stepIndex);
      var stack = this.getChildControl("stack");

      if (!stack[stepIndex]) {
        this.__createAndAddStepWidget(stepIndex);
      }
      stack.setSelection([stack.getChildren()[stepIndex]]);
    },

    /**
     * @param stepIndex {Integer} >= 0
     */
    __createAndAddStepWidget : function(stepIndex) {
      qx.core.Assert.assertPositiveInteger(stepIndex);
      qx.core.Assert.assertUndefined(this.getChildControl("stack").getChildren()[stepIndex]);

      var w = new qx.ui.basic.Label("" + stepIndex);
      this.getChildControl("stack").addAt(w, stepIndex);
    },

    // overridden
    _createChildControlImpl : function(id) {
      var control;

      switch(id) {
        case "sidebar":
          control = new qx.ui.basic.Label("TODO: sidebar");
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
