/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Dashboard widget that can start a single workflow
 */
qx.Class.define("gosa.plugins.workflowstarter.Main", {
  extend : gosa.plugins.AbstractDashboardWidget,

  construct : function() {
    this.base(arguments);
    var layout = new qx.ui.layout.Atom();
    layout.setCenter(true);
    this.getChildControl("content").setLayout(layout);
    this.getChildControl("content").addListener("tap", function() {
      gosa.ui.controller.Objects.getInstance().startWorkflow(this.getChildControl("workflow-item"));
    }, this);
  },

  /*
   *****************************************************************************
   PROPERTIES
   *****************************************************************************
   */
  properties : {
    appearance: {
      refine: true,
      init: "gosa-dashboard-widget-workflowstarter"
    },

    /**
     * Maximum number of items to show
     */
    workflow: {
      check: "String",
      nullable: true,
      apply: "_applyWorkflow",
      event: "changeWorkflow"
    }
  },

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */
  members : {
    _listController: null,

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "workflow-item":
          control = new gosa.ui.form.WorkflowItem();
          this.bind("workflow", control, "id");
          control.getChildControl("content").getLayout().setAlignX("center");
          this.getChildControl("content").add(control);
          break;

      }
      return control || this.base(arguments, id);
    },

    _applyWorkflow: function(value) {
      var item = this.getChildControl("workflow-item");
      item.setLoading(true);
      gosa.io.Rpc.getInstance().cA("getWorkflowDetails", value)
      .then(function(workflowDetails) {
        item.setLabel(workflowDetails.name);
        // item.setDescription(workflowDetails.description);
        item.setIcon(workflowDetails.icon);
      }, this)
      .catch(function(error) {
        this.error(error);
        item.setLabel(error.getData().message);
      }, this)
      .finally(function() {
        item.setLoading(false);
      }, this);
    },

    draw: function() {}

  },

  defer: function () {
    gosa.data.DashboardController.registerWidget(gosa.plugins.workflowstarter.Main, {
      displayName: qx.locale.Manager.tr("Workflow starter"),
      icon: "@Ligature/magic",
      defaultColspan: 1,
      defaultRowspan: 2,
      resizable: false,
      theme: {
        appearance : gosa.plugins.workflowstarter.Appearance
      },
      settings: {
        mandatory: ["workflow"],
        types: {
          workflow: {
            type: "selection",
            provider: "RPC",
            method: "getWorkflows",
            key: "KEY",
            value: "name",
            icon: "icon"
          }
        }
      }
    });
  }
});