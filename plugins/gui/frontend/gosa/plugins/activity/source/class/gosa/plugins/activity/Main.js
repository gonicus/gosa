/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Dashboard widget that shows the last changed objects
 */
qx.Class.define("gosa.plugins.activity.Main", {
  extend : gosa.plugins.AbstractDashboardWidget,

  construct : function() {
    this.base(arguments);
    this.getChildControl("title").setValue(this.tr("Recently changed items"));
    this.getChildControl("container").setLayout(new qx.ui.layout.VBox());
    this._model = new gosa.plugins.activity.model.SearchResult();

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
      init: "gosa-dashboard-widget-activities"
    },
    /**
     * Maximum number of items to show
     */
    maxItems: {
      check: "Number",
      init: 10
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
          item.addListener("edit", function(e) {
            item.setIsLoading(true);
            gosa.ui.controller.Objects.getInstance().openObject(e.getData().getDn())
            .finally(function() {
              item.setIsLoading(false);
            });
          }, this);

          item.addListener("remove", function(e) {
            var dialog = new gosa.ui.dialogs.RemoveObject(e.getData().getDn());
            dialog.addListener("remove", function() {
              gosa.proxy.ObjectFactory.removeObject(item.getUuid());
            }, this);
            dialog.open();

          }, this);
          return (item);
        }.bind(this),

        configureItem: function(item) {
          item.set({
            appearance: "gosa-plugins-actitivies-item"
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

    refreshModel: function() {
      if (this.isSeeable()) {
        gosa.io.Rpc.getInstance().cA("search", gosa.Session.getInstance().getBase(), "sub", null, {
          'fallback' : true,
          'order-by' : "last-changed",
          'order' : "desc",
          'limit' : this.getMaxItems(),
          'secondary' : false
        })
        .then(this._model.updateModel, this._model)
        .catch(function(error) {
          this.error(error);
          var d = new gosa.ui.dialogs.Error(error);
          d.open();
        }, this)
        .finally(function() {
          this.__updateQueued = false;
        }, this);
      } else {
        this.__updateQueued = true;
      }
    }
  },

  /*
   *****************************************************************************
   DESTRUCTOR
   *****************************************************************************
   */
  destruct : function() {
    gosa.io.Sse.getInstance().removeListener("objectModified", this.refreshModel, this);
    gosa.io.Sse.getInstance().removeListener("objectCreated", this.refreshModel, this);
    gosa.io.Sse.getInstance().removeListener("objectRemoved", this.refreshModel, this);
  },

  defer: function () {
    gosa.data.controller.Dashboard.registerWidget(gosa.plugins.activity.Main, {
      displayName: qx.locale.Manager.tr("Activities"),
      icon: "@Ligature/exchange",
      theme: {
        appearance : gosa.plugins.activity.Appearance
      },
      defaultColspan: 3,
      defaultRowspan: 5
    });
  }
});