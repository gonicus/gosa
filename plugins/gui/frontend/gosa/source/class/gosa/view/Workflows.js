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

qx.Class.define("gosa.view.Workflows",
{
  extend : qx.ui.tabview.Page,
  type: "singleton",

  construct : function()
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", "@Ligature/app");
    this.getChildControl("button").getChildControl("label").exclude();
    this.setLayout(new qx.ui.layout.VBox(5));
    this._rpc = gosa.io.Rpc.getInstance();
    this._createChildControl("list");

    this.addListener("appear", this.__reload, this);
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
          var item = result[id];
          item.id = id;
          this._marshaler.toClass(item, true);
          data.push(this._marshaler.toModel(item, true));
        }
        this._listController.setModel(data);
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
  }
});
