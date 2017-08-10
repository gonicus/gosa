/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 *
 */
qx.Class.define("gosa.plugins.objectlist.Main", {
  extend : gosa.plugins.AbstractDashboardWidget,

  construct : function() {
    this.base(arguments);

    this.getChildControl("container").setLayout(new qx.ui.layout.VBox());
    this._model = new gosa.plugins.objectlist.model.SearchResult();

    this.rpc = gosa.io.Rpc.getInstance();

    // Listen for object changes coming from the backend
    gosa.io.Sse.getInstance().addListener("objectModified", this.refreshModel, this);
    gosa.io.Sse.getInstance().addListener("objectCreated", this.refreshModel, this);
    gosa.io.Sse.getInstance().addListener("objectRemoved", this.refreshModel, this);

    this.addListener("appear", function() {
      if (this.__updateQueued === true) {
        this.refreshModel();
      }
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
      init: "gosa-dashboard-widget-objectlist"
    },
    /**
     * Maximum number of items to show
     */
    maxItems: {
      check: "Number",
      init: 10
    },

    query: {
      check: "String",
      init: "",
      apply: "_applyQuery"
    },

    startWorkflow: {
      check: "String",
      nullable: true
    }
  },

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */
  members : {
    _listController: null,
    __updateQueued: null,

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "list":
          control = new qx.ui.list.List();
          control.setDelegate(this.__getListDelegate());
          this.getChildControl("content").add(control);
          break;
      }

      return control || this.base(arguments, id);
    },

    __getListDelegate: function() {
      return {
        createItem : function() {

          var item = new gosa.ui.SearchListItem();
          item.setToolbarEnabled(false);
          item.addListener("tap", function(e) {
            if (this.getStartWorkflow()) {
              var dn = e.getCurrentTarget().getModel().getDn();
              console.log(dn);
              // TODO: start workflow with dn as parameter
              var workflow = new gosa.ui.form.WorkflowItem(true);
              workflow.bind("loading", item, "isLoading");
              workflow.setId(this.getStartWorkflow());
              gosa.ui.controller.Objects.getInstance().startWorkflow(workflow);
            }
          }, this);
          return (item);
        }.bind(this),

        configureItem: function(item) {
          item.set({
            appearance: "gosa-plugins-objectlist-item"
          });
          this.getChildControl("container").bind("enabled", item.getChildControl("dn"), "selectable");
        }.bind(this),

        bindItem : function(controller, item, id) {
          controller.bindProperty("title", "title", null, item, id);
          controller.bindProperty("type", "type", null, item, id);
          controller.bindProperty("dn", "dn", null, item, id);
          controller.bindProperty("uuid", "uuid", null, item, id);
          controller.bindProperty("description", "description", null, item, id);
          controller.bindProperty("icon", "icon", null, item, id);
          controller.bindProperty("", "model", null, item, id);
        },

        sorter : function(a, b) {
          return (b.getLastChanged().toTimeStamp() - a.getLastChanged().toTimeStamp());
        }
      }
    },

    draw: function() {
      this._model.bind("model", this.getChildControl("list"), "model");
      this.refreshModel();
    },

    // property apply
    _applyQuery: function() {
      this.refreshModel();
    },

    refreshModel: function() {
      if (this.isSeeable()) {
        var query = this.getQuery();
        if (query.length <= 2) {
          // do not search
          this._model.updateModel([]);
        } else {
          var args = [];
          if (query.startsWith("RPC:")) {
            var parts = query.split(":");
            // skip the RPC part
            parts.shift();
            query = null;
            args = parts;
          } else {
            // normal search query
            args = ["search", gosa.Session.getInstance().getBase(), "sub", query, {
              'fallback' : true,
              'limit' : this.getMaxItems(),
              'secondary' : false
            }];
          }
          if (args.length > 0) {
            this.rpc.cA.apply(this.rpc, args)
            .then(this._model.updateModel, this._model)
            .catch(function(error) {
              this.error(error);
              var d = new gosa.ui.dialogs.Error(error);
              d.open();
            }, this)
            .finally(function() {
              this.__updateQueued = false;
            }, this);
          }
        }
      } else {
        this.__updateQueued = true;
      }
    }
  },

  defer: function () {
    gosa.data.controller.Dashboard.registerWidget(gosa.plugins.objectlist.Main, {
      displayName: qx.locale.Manager.tr("ObjectList"),
      defaultColspan: 3,
      defaultRowspan: 1,
      theme: {
        appearance : gosa.plugins.objectlist.Appearance
      },
      settings: {
        mandatory: ["query"],
        properties: {
          title: {
            type: "String",
            title: qx.locale.Manager.tr("Title")
          },
          query: {
            // simple search string or an an RPC (RPC:<command-name>:param1:param2:..)
            type: "String",
            title: qx.locale.Manager.tr("Search query"),
            multiline: true
          },
          maxItems: {
            type: "Number",
            title: qx.locale.Manager.tr("Limit"),
            minValue: 1,
            maxValue: 100
          },
          startWorkflow: {
            title: qx.locale.Manager.tr("Start workflow"),
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