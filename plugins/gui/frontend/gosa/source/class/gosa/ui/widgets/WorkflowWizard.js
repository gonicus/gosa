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
 * Container showing several tabs - all necessary for displaying forms for editing an object.
 */
qx.Class.define("gosa.ui.widgets.WorkflowWizard", {

  extend: qx.ui.core.Widget,

  /**
   * @param workflowObject {gosa.proxy.Object}
   * @param controller {gosa.data.controller.Workflow}
   * @param templates {Array}
   */
  construct: function(workflowObject, controller, templates) {
    this.base(arguments);
    this._setLayout(new qx.ui.layout.HBox(18));

    qx.core.Assert.assertArray(templates);
    qx.core.Assert.assertInstance(controller, gosa.data.controller.Workflow);
    qx.core.Assert.assertInstance(workflowObject, gosa.proxy.Object);

    this.__stepsConfig = [];
    this.__contexts = [];
    this.__controller = controller;
    this.__modelWidgetConnector = new gosa.data.ModelWidgetConnector(workflowObject, this);
    this.__enterCommand = new qx.ui.command.Command("Enter");
    this.__enterCommand.addListener("execute", this.__onEnterPress, this);

    this.__fillStepsConfiguration(templates);
    this.__fillSideBar();
    this.__createButtons();
    this.__showStep(0);
  },

  events : {
    "close" : "qx.event.type.Event"
  },

  properties : {
    appearance : {
      refine : true,
      init : "workflow-wizard"
    }
  },

  members : {
    __controller : null,
    __contexts : null,
    __currentStep : 0,
    __modelWidgetConnector : null,
    __enterCommand : null,

    /**
     * @type {Array} Holds information for the single steps. The order is in which to show the steps. There is one
     * element for each step. Each element is an object with the following attributes:
     *
     * id          : a string identifying the step (e.g. "user-shadow")
     * name        : (human-readable) name of the step
     * description : a short text describing the step
     * template    : the compiled template
     */
    __stepsConfig : null,

    getContexts : function() {
      return this.__contexts;
    },

    validate : function() {
      var valid = this.__contexts.every(function(context) {
        var widgetMap = context.getWidgetRegistry().getMap();
        for (var attributeName in widgetMap) {
          if (widgetMap.hasOwnProperty(attributeName) &&
              !widgetMap[attributeName].isValid() &&
              !widgetMap[attributeName].isBlocked()) {
            return false;
          }
        }
        return true;
      }, this);

      this.getChildControl("next-button").setEnabled(valid);
      this.getChildControl("save-button").setEnabled(valid);
    },

    __onEnterPress : function() {
      var saveButton = this.getChildControl("save-button");
      if (saveButton.isVisible() && saveButton.isEnabled()) {
        saveButton.execute();
        return;
      }

      var nextButton = this.getChildControl("next-button");
      if (nextButton.isVisible() && nextButton.isEnabled()) {
        nextButton.execute();
      }
    },

    __onCancel : function() {
      var dialog = new gosa.ui.dialogs.Confirmation(
        this.tr("Really abort?"),
        this.tr("All entered data will be lost. Are you sure you want to abort?")
      );
      dialog.setAutoDispose(true);
      dialog.addListenerOnce("confirmed", function(event) {
        if (event.getData()) {
          this.__controller.close();
        }
      }, this);
      dialog.open();
    },

    __nextStep : function() {
      this.__showStep(this.__currentStep + 1);
    },

    __previousStep : function() {
      this.__showStep(this.__currentStep - 1);
    },

    __showStep : function(index) {
      qx.core.Assert.assertInRange(index, 0, this.__stepsConfig.length - 1,
                                   qx.locale.Manager.tr("Workflow step index out of bounds %1", index));

      var stack = this.getChildControl("stack");
      if (!stack.getChildren()[index]) {
        this.__createStepWidget(index);
      }
      stack.setSelection([stack.getChildren()[index]]);

      stack.getChildren()[index].addListenerOnce("appear", function() {
        this.__modelWidgetConnector.connectAll();
        this.validate();
      }, this);
      this.__currentStep = index;

      var children = this.getChildControl("sidebar").getChildren();
      for (var i=0, l=children.length; i<l; i++) {
        children[i].setDone(i < index);
        children[i].setActive(index === i);
      }

      this.__updateButtons();
    },

    __updateButtons : function() {
      this.getChildControl("previous-button").setEnabled(this.__currentStep > 0);
      this.getChildControl("next-button").setEnabled(this.__currentStep < this.__stepsConfig.length - 1);
      this.__showSaveButton(this.__currentStep === this.__stepsConfig.length - 1);
    },

    __createStepWidget : function(stepIndex) {
      qx.core.Assert.assertUndefined(this.getChildControl("stack").getChildren()[stepIndex]);

      var container = new qx.ui.container.Composite(new qx.ui.layout.VBox());
      qx.core.Assert.assertUndefined(this.__contexts[stepIndex]);
      this.__contexts[stepIndex] = new gosa.engine.Context(this.__stepsConfig[stepIndex].template,
                                                           container, undefined, this.__controller);
      this.getChildControl("stack").addAt(container, stepIndex);
    },

    __fillStepsConfiguration : function(templates) {
      templates.forEach(function(config) {
        this.__stepsConfig.push({
          id          : config.extension,
          template    : config.template,
          name        : gosa.util.Template.getValueAtPath(config.template, ["name"]),
          description : gosa.util.Template.getValueAtPath(config.template, ["description"])
        });
      }, this);
    },

    __fillSideBar : function() {
      var last;
      this.__stepsConfig.forEach(function(item, index) {
        var item = last = new gosa.ui.form.ProgressItem(index + 1, item.name, item.description);
        this.getChildControl("sidebar").add(item);
      }, this);

      last.addState("last");
    },

    __showSaveButton : function(shallShow) {
      this.getChildControl("save-button").setVisibility(shallShow ? "visible" : "excluded");
      this.getChildControl("next-button").setVisibility(shallShow ? "excluded" : "visible");
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
          this._add(control, {flex: 1});
          break;

        case "sidebar":
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox());
          this._add(control);
          break;

        case "stack":
          control = new qx.ui.container.Stack();
          this.getChildControl("form-container").addAt(control, 0, {flex: 1});
          break;

        case "button-group":
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox(8));
          this.getChildControl("form-container").addAt(control, 1);
          break;

        case "cancel-button":
          control = new qx.ui.form.Button(this.tr("Cancel"));
          control.addListener("execute", this.__onCancel, this);
          this.getChildControl("button-group").add(control);
          this.getChildControl("button-group").add(new qx.ui.core.Spacer(), {flex: 1});
          break;

        case "next-button":
          control = new qx.ui.form.Button(this.tr("Next"));
          control.addListener("execute", this.__nextStep, this);
          this.getChildControl("button-group").add(control);
          break;

        case "previous-button":
          control = new qx.ui.form.Button(this.tr("Previous"));
          control.addListener("execute", this.__previousStep, this);
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
    this._disposeArray("__contexts");
    this._disposeObjects("__modelWidgetConnector", "__enterCommand");
    this.__controller = null;
    this.__stepsConfig = null;
  }
});
