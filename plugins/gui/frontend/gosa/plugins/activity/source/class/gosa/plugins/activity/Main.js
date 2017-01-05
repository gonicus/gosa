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
    this._model = new gosa.data.model.SearchResult();
  },

  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    /**
     * Global identifier of this widget must be in format
     * <pre>type:name</pre>
     *   Where 'type' is one of source, ext
     *   and 'name' consist of any word character and '_'.
     *
     *   'type' determines from where this widget can be loaded
     *   <ul>
     *     <li>source: this widget is included in the main projects sources</li>
     *     <li>ext: this widget has been loaded from an external source (as part or via user upload)</li>
     *   </ul>
     */
    ID: "ext:dashboard_plugin_activity"
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
              gosa.ui.controller.Objects.getInstance().removeObject(item.getUuid());
            }, this);
            dialog.open();

          }, this);
          return (item);
        }.bind(this),

        configureItem: function(item) {
          item.set({
            appearance: "gosa-plugins-actitivies-item"
          })
        },

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
          return (a.getLastChanged().toTimeStamp() - b.getLastChanged().toTimeStamp());
        }
      }
    },

    draw: function() {
      this._model.bind("model", this.getChildControl("list"), "model");

      gosa.io.Rpc.getInstance().cA("search", gosa.Session.getInstance().getBase(), "sub", null, {
        'fallback'  : true,
        'order-by'  : "last-changed",
        'order'     : "desc",
        'limit'     : this.getMaxItems()
      })
      .then(this._model.updateModel, this._model)
      .catch(function(error) {
        this.error(error);
        var d = new gosa.ui.dialogs.Error(error);
        d.open();
      }, this);
    }
  },

  defer: function () {
    gosa.view.Dashboard.registerWidget(gosa.plugins.activity.Main, {
      displayName: qx.locale.Manager.tr("Activities"),
      theme: {
        appearance : gosa.plugins.activity.Appearance
      },
      defaultColspan: 3
    });
  }
});