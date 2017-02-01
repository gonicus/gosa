/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Controller for the {@link gosa.ui.widget.WorkflowWizard} widget; connects it to the model.
 */
qx.Class.define("gosa.data.controller.Workflow", {

  extend : qx.core.Object,

  /**
   * @param workflowObject {gosa.proxy.Object}
   * @param widget {gosa.ui.widgets.WorkflowWizard}
   * @param templates {Array}
   */
  construct : function(workflowObject, widget, templates) {
    this.base(arguments);

    this.__workflowObject = workflowObject;
    this.__widget = widget;
    this.__stepsConfig = [];
    this.__contexts = [];
    this.__fillStepsConfiguration(templates);

    this.__widget.setController(this);
    this.__showStep(0);

    this.__widget.addListenerOnce("close", this.dispose, this);
  },

  members : {
    /**
     * @type {gosa.proxy.Object}
     */
    __workflowObject : null,

    /**
     * @type {gosa.ui.widgets.WorkflowWizard}
     */
    __widget : null,

    /**
     * @type {Array} Holds information for the single steps. The order is in which to show the steps. There is one
     * element for each step. Each element is an object with the following attributes:
     *
     * id : a string identifying the step (e.g. "user-shadow")
     * name : (human-readable) name of the step
     * description : a short text describing the step
     * template : the compiled template
     */
    __stepsConfig : null,

    /**
     * @type {Array} Holds the {@link gosa.engine.Context} for each step index
     */
    __contexts : null,

    /**
     * @type {Integer} Index of the current step
     */
    __currentStep : 0,

    /**
      * @return {Array | null} List of all attributes of the object
    */
    getAttributes : function() {
      return qx.lang.Type.isArray(this.__workflowObject.attributes) ? this.__workflowObject.attributes : null;
    },

    /**
     * Summons the data necessary for the side (navigation) bar of the wizard.
     *
     * @return {Array} Objects with "name" and "description"; has the correct order for steps
     */
    getSideBarData : function() {
      return this.__stepsConfig.map(function(item) {
        return {
          name : item.name,
          description : item.description
        };
      });
    },

    /**
     * Creates a context (and therefore the widgets) for the given index.
     *
     * @param stepIndex {Integer}
     * @param rootWidget {qx.ui.container.Composite} Where the widgets of the template should go in
     */
    createContextForIndex : function(stepIndex, rootWidget) {
      qx.core.Assert.assertUndefined(this.__contexts[stepIndex]);
      this.__contexts[stepIndex] = new gosa.engine.Context(this.__stepsConfig[stepIndex].template, rootWidget,
        undefined, this);
    },

    saveAndClose : function() {
      console.warn("TODO: save workflow");
      this.close();
    },

    close : function() {
      this.__workflowObject.close();
      this.__widget.close();
      this.dispose();
    },

    nextStep : function() {
      this.__showStep(this.__currentStep + 1);
    },

    previousStep : function() {
      this.__showStep(this.__currentStep - 1);
    },

    __showStep : function(index) {
      qx.core.Assert.assertInRange(index, 0, this.__stepsConfig.length - 1,
        qx.locale.Manager.tr("Workflow step index out of bounds %1", index));
      this.__widget.showStep(index);
      this.__currentStep = index;

      this.__updateButtons();
    },

    __updateButtons : function() {
      this.__widget.getChildControl("previous-button").setEnabled(this.__currentStep > 0);
      this.__widget.getChildControl("next-button").setEnabled(this.__currentStep < this.__stepsConfig.length - 1);
      this.__widget.setShowSaveButton(this.__currentStep === this.__stepsConfig.length - 1);
    },

    /**
     * @param templates {Array}
     */
    __fillStepsConfiguration : function(templates) {
      templates.forEach(this.__fillStepInformation, this);
    },

    /**
     * @param config {Object}
     */
    __fillStepInformation : function(config) {
      this.__stepsConfig.push({
        id : config.extension,
        template : config.template,
        name : gosa.util.Template.getValueAtPath(config.template, ["name"]),
        description : gosa.util.Template.getValueAtPath(config.template, ["description"])
      });
    }
  },

  destruct : function() {
    this._disposeArray("__contexts");
    this.__workflowObject = null;
    this.__widget = null;
    this.__stepsConfig = null;
  }
});
