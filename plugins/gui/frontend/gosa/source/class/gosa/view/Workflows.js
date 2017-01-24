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
  extend : qx.ui.tabview.Page,
  include: gosa.upload.MDragUpload,
  type: "singleton",

  construct : function()
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", "@Ligature/magic");
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

    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "list":
          control = new qx.ui.container.Composite(new gosa.ui.layout.Flow());
          this._listController = new gosa.data.controller.EnhancedList(null, control, "name");
          this._listController.setDelegate(this._getListDelegate());
          this.add(control, {flex: 1});
          break;

        case "upload-dropbox":
          control = new qx.ui.container.Composite(new qx.ui.layout.Atom().set({center: true}));
          var dropBox = new qx.ui.basic.Atom(this.tr("Drop file here to add it to the available workflows."), "@Ligature/upload/128");
          dropBox.set({
            allowGrowY: false
          });
          control.addListener("appear", function() {
            var element = control.getContentElement().getDomElement();
            element.ondrop = function(e) {
              gosa.util.DragDropHelper.getInstance().onHtml5Drop.call(gosa.util.DragDropHelper.getInstance(), e, "workflow");
              this.setUploadMode(false);
              return false;
            }.bind(this);

            element.ondragover = function(ev) {
              ev.preventDefault();
            };
          }, this);
          control.add(dropBox);
          control.exclude();
          qx.core.Init.getApplication().getRoot().add(control, {edge: 0});
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

      return control || this.base(arguments, id);
    },

    _getListDelegate: function() {
      return {
        createItem: function() {
          return new gosa.ui.form.WorkflowItem();
        },

        configureItem: function(item) {
          item.addListener("tap", function() {
            gosa.ui.controller.Objects.getInstance().startWorkflow(item);
          });
        },

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
