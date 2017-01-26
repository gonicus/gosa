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

qx.Class.define("gosa.view.Workflows", {
  extend : gosa.view.AbstractEditableView,
  include: [gosa.upload.MDragUpload, gosa.util.MMethodChaining],
  type: "singleton",

  construct : function()
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", "@Ligature/magic");
    this.setUploadType("workflow");
    this.setUploadHint(this.tr("Drop file here to add it to the available workflows."));
    this.getChildControl("button").getChildControl("label").exclude();
    this.setLayout(new qx.ui.layout.VBox(5));
    this._rpc = gosa.io.Rpc.getInstance();
    this._createChildControl("list");

    this.addListener("appear", this.__reload, this);
    gosa.io.Sse.getInstance().addListener("workflowUpdate", this.__reload, this);
  },
  /*
   *****************************************************************************
   PROPERTIES
   *****************************************************************************
   */
  properties : {
    appearance: {
      refine: true,
      init: "gosa-tabview-page-workflows"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __toolbarButtons: null,
    _listController : null,

    /**
     * Load the available Workflows and initialize the view
     * @private
     */
    __reload: function() {
      this._marshaler = new qx.data.marshal.Json();
      this._rpc.cA("getWorkflows").then(function(result) {
        var data = new qx.data.Array();
        for (var id in result) {
          if (result.hasOwnProperty(id)) {
            var item = result[id];
            item.id = id;
            this._marshaler.toClass(item, true);
            data.push(this._marshaler.toModel(item, true));
          }
        }
        this._listController.setModel(data);
        if (data.length) {
          this.getChildControl("empty-info").exclude();
        } else {
          this.getChildControl("empty-info").show();
        }
      }, this)
      .catch(function(error) {
        this.error(error);
        new gosa.ui.dialogs.Error(error).open();
      });
    },

    __deleteWorkflow: function(item) {
      gosa.io.Rpc.getInstance().cA("removeWorkflow", item.getId())
      .then(function() {
        this.setSelectedWidget(null);
      }, this)
      .catch(function(error) {
        this.error(error.getData().message);
        gosa.ui.dialogs.Error.show(error);
      }, this);
    },

    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "list":
          control = new qx.ui.container.Composite(new gosa.ui.layout.Flow());
          this._listController = new gosa.data.controller.EnhancedList(null, control, "name");
          this._listController.setDelegate(this._getListDelegate());
          this.add(control, {flex: 1});
          break;

        case "empty-info":
          var label = new qx.ui.basic.Label(this.tr("Please add a workflow dragging a workflow zip file into this window"));
          control = new qx.ui.container.Composite(new qx.ui.layout.Atom().set({center: true}));
          control.add(label);
          control.exclude();
          control.addListener("changeVisibility", function(ev) {
            if (ev.getData() === "visible") {
              this.getChildControl("list").exclude();
            } else {
              this.getChildControl("list").show();
            }
          }, this);
          this._addAt(control, 2, {flex: 1});
          break;
      }
      if (!control) {
        control = this.processHooks("after", "_createChildControlImpl", id);
      }

      return control || this.base(arguments, id);
    },

    // property apply
    _applyUploadMode: function(value) {
      if (value)  {
        this.getChildControl("list").exclude();
      } else {
        this.getChildControl("list").show();
      }
    },

    _getListDelegate: function() {
      return {
        createItem: function() {
          return new gosa.ui.form.WorkflowItem();
        },

        configureItem: function(item) {
          item.addListener("tap", this._onTap, this);
        }.bind(this),

        bindItem: function(controller, item , index) {
          controller.bindProperty("name", "label", null, item, index);
          controller.bindProperty("icon", "icon", {
            converter: function(value) {
              return value || "@Ligature/app"
            }
          }, item, index);
          controller.bindProperty("description", "description", null, item, index);
          controller.bindProperty("id", "id", null, item, index);
          if (index === 0) {
            item.addState("first");
          } else {
            item.removeState("first");
          }
        },

        group: function(item) {
          return item.getCategory();
        }
      }
    },

    // overridden
    _applyEditMode: function(value) {
      this.base(arguments, value);
      if (value === true) {
        this.getChildControl("empty-info").exclude();
      }
    },

    _onTap: function(ev) {
      if (this.isEditMode()) {
        if (ev.getCurrentTarget() instanceof gosa.ui.form.WorkflowItem) {
          this.setSelectedWidget(ev.getCurrentTarget());
          ev.stopPropagation();
        }
        else {
          this.setSelectedWidget(null);
        }
      } else {
        gosa.ui.controller.Objects.getInstance().startWorkflow(ev.getCurrentTarget());
      }
    },

    // overridden
    _applySelectedWidget: function(value, old) {
      this.base(arguments, value, old);
      if (value) {
        this.__toolbarButtons['delete'].setEnabled(true);
      } else {
        this.__toolbarButtons['delete'].setEnabled(false);
      }
    },

    // overridden
    _fillToolbar: function(toolbar) {
      this.__toolbarButtons = {};

      var uploadButton = new com.zenesis.qx.upload.UploadButton(this.tr("Upload"), "@Ligature/upload");
      uploadButton.setAppearance("button-link");

      gosa.io.Rpc.getInstance().cA("registerUploadPath", "workflow")
      .then(function(result) {
        var path = result[1];
        new gosa.util.UploadMgr(uploadButton, path);
      }, this);

      // add button
      toolbar.add(uploadButton);
      this.__toolbarButtons["upload"] = uploadButton;

      // delete button
      var widget = new qx.ui.form.Button(this.tr("Delete"), "@Ligature/trash");
      widget.setDroppable(true);
      widget.setEnabled(false);
      widget.setAppearance("button-link");
      widget.addListener("tap", function() {
        if (this.getSelectedWidget()) {
          this.__deleteWorkflow(this.getSelectedWidget());
        }
      }, this);
      widget.addListener("drop", function(ev) {
        this.__deleteWidget(ev.getRelatedTarget());
        this.__draggedWidget = null;
      }, this);
      widget.addListener("dragover", function(ev) {
        qx.bom.element.Animation.animate(ev.getTarget().getContentElement().getDomElement(), gosa.util.AnimationSpecs.HIGHLIGHT_DROP_TARGET);
      }, this);
      widget.addListener("dragleave", function(ev) {
        qx.bom.element.Animation.animate(ev.getTarget().getContentElement().getDomElement(), gosa.util.AnimationSpecs.UNHIGHLIGHT_DROP_TARGET);
      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["delete"] = widget;

      // abort editing
      widget = new qx.ui.form.Button(this.tr("Abort"), "@Ligature/ban/22");
      widget.setAppearance("button-link");
      widget.addListener("execute", function() {
        this.toggleEditMode();
      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["cancel"] = widget;
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    gosa.io.Sse.getInstance().removeListener("workflowUpdate", this.__reload, this);
  }
});
