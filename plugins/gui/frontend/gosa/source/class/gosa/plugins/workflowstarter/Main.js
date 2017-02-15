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
 * Dashboard widget that can start a single workflow
 */
qx.Class.define("gosa.plugins.workflowstarter.Main", {
  extend : gosa.plugins.AbstractDashboardWidget,

  construct : function() {
    this.base(arguments);
    this.addListener("tap", function() {
      if (this.getChildControl("content").isEnabled()) {
        gosa.ui.controller.Objects.getInstance().startWorkflow(this.getChildControl("workflow-item"));
      }
    }, this);

    // Add listeners
    this.addListener("pointerover", this._onPointerOver);
    this.addListener("pointerout", this._onPointerOut);
    this.addListener("pointerdown", this._onPointerDown);
    this.addListener("pointerup", this._onPointerUp);

    this.addListener("layoutChanged", this._onLayoutChanged, this);

    gosa.view.Dashboard.getInstance().addListener("cellWidthChanged", this.__updateDescriptionWidth, this);
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
    __grid: null,

    _forwardStates: {
      hovered: false
    },

    /*
    ---------------------------------------------------------------------------
      EVENT LISTENERS
    ---------------------------------------------------------------------------
    */

    _onLayoutChanged: function() {
      if (!this.__grid) {
        this.__grid = this.getLayoutParent().getLayout();
      }
      this.__updateDescriptionWidth();
      var props = this.getLayoutProperties();
      var control = this.getChildControl("workflow-item");
      if (props.colSpan === 2) {
        // wide mode => show description and icon on left position
        control.getChildControl("description").show();
        control.setIconPosition("left");
      } else if (props.colSpan === 1) {
        // small mode => no description and icon on top
        control.getChildControl("description").exclude();
        control.setIconPosition("top");
      }
      // cellHeight
      var rowSpan = props.rowSpan||1;
      var cellHeight = this.__grid.getRowHeight(props.row) * rowSpan + this.__grid.getSpacingY() * (rowSpan - 1);
      this.setMaxHeight(cellHeight);
    },

    __updateDescriptionWidth: function() {
      if (!this.__grid) {
        this.__grid = this.getLayoutParent().getLayout();
      }
      var control = this.getChildControl("workflow-item").getChildControl("description");
      var props = this.getLayoutProperties();
      var colSpan = props.colSpan || 1;
      var cellWidth = this.__grid.getColumnWidth(props.column) * colSpan + this.__grid.getSpacingX() * (colSpan -1);
      control.setMaxWidth(cellWidth - 105);
    },

    /**
     * Listener method for "pointerover" event
     * <ul>
     * <li>Adds state "hovered"</li>
     * <li>Removes "abandoned" and adds "pressed" state (if "abandoned" state is set)</li>
     * </ul>
     *
     * @param e {Event} Mouse event
     */
    _onPointerOver : function(e)
    {
      if (!this.isEnabled() || e.getTarget() !== this) {
        return;
      }

      if (this.hasState("abandoned"))
      {
        this.removeState("abandoned");
        this.addState("pressed");
      }

      this.addState("hovered");
    },

    /**
     * Listener method for "pointerout" event
     * <ul>
     * <li>Removes "hovered" state</li>
     * <li>Adds "abandoned" and removes "pressed" state (if "pressed" state is set)</li>
     * </ul>
     *
     * @param e {Event} Mouse event
     */
    _onPointerOut : function(e)
    {
      if (!this.isEnabled() || e.getTarget() !== this) {
        return;
      }

      this.removeState("hovered");

      if (this.hasState("pressed"))
      {
        this.removeState("pressed");
        this.addState("abandoned");
      }
    },

    /**
     * Listener method for "pointerdown" event
     * <ul>
     * <li>Removes "abandoned" state</li>
     * <li>Adds "pressed" state</li>
     * </ul>
     *
     * @param e {Event} Mouse event
     */
    _onPointerDown : function(e)
    {
      if (!e.isLeftPressed()) {
        return;
      }

      e.stopPropagation();

      // Activate capturing if the button get a pointerout while
      // the button is pressed.
      this.capture();

      this.removeState("abandoned");
      this.addState("pressed");
    },

     /**
     * Listener method for "pointerup" event
     * <ul>
     * <li>Removes "pressed" state (if set)</li>
     * <li>Removes "abandoned" state (if set)</li>
     * <li>Adds "hovered" state (if "abandoned" state is not set)</li>
     *</ul>
     *
     * @param e {Event} Mouse event
     */
    _onPointerUp : function(e)
    {
      this.releaseCapture();

      // We must remove the states before executing the command
      // because in cases were the window lost the focus while
      // executing we get the capture phase back (mouseout).
      var hasPressed = this.hasState("pressed");
      var hasAbandoned = this.hasState("abandoned");

      if (hasPressed) {
        this.removeState("pressed");
      }

      if (hasAbandoned) {
        this.removeState("abandoned");
      }

      e.stopPropagation();
    },


    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "workflow-item":
          control = new gosa.ui.form.WorkflowItem(true);
          this.bind("workflow", control, "id");
          var layout = new qx.ui.layout.Atom();
          layout.setCenter(true);
          this.getChildControl("content").setLayout(layout);
          this.getChildControl("content").add(control);
          this.getChildControl("content").setAnonymous(true);
          control.setAnonymous(true);
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
        item.setDescription(workflowDetails.description);
        item.setIcon(workflowDetails.icon);
        this._onLayoutChanged();
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

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this.__grid = null;
    gosa.view.Dashboard.getInstance().removeListener("cellWidthChanged", this.__updateDescriptionWidth, this);
  },

  defer: function () {
    gosa.data.controller.Dashboard.registerWidget(gosa.plugins.workflowstarter.Main, {
      displayName: qx.locale.Manager.tr("Workflow starter"),
      icon: "@Ligature/magic",
      defaultColspan: 1,
      defaultRowspan: 2,
      maxColspan: 2,
      resizable: [false, true, false, false],
      theme: {
        appearance : gosa.plugins.workflowstarter.Appearance
      },
      settings: {
        mandatory: ["workflow"],
        properties: {
          workflow: {
            title: qx.locale.Manager.tr("Workflow"),
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