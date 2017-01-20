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
qx.Class.define("gosa.plugins.yql.Main", {
  extend : gosa.plugins.AbstractDashboardWidget,

  construct : function() {
    this.base(arguments);
  },

  /*
   *****************************************************************************
   PROPERTIES
   *****************************************************************************
   */
  properties : {
    appearance: {
      refine: true,
      init: "gosa-dashboard-widget-yql"
    },

    query: {
      check: "String",
      init: "",
      apply: "_applyQuery"
    },

    mapping: {
      check: "Object",
      init: {},
      transform: "string2json"
    },

    /**
     * refresh rate in seconds
     */
    refreshRate: {
      check: "Number",
      init: 360,
      event: "changeRefreshRate"
    }
  },

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */
  members : {
    __store: null,
    __timer: null,

    draw: function() {
      // add your code here
    },

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "list":
          control = new qx.ui.list.List();
          control.setLabelPath("title");
          this.getChildControl("content").add(control);
          break;
      }

      return control || this.base(arguments, id);
    },

    string2json: function(value) {
      if (!value) {
        return {};
      }
      return qx.lang.Type.isString(value) ? qx.lang.Json.parse(value) : value;
    },

    // property apply
    _applyQuery: function(value) {
      if (value) {
        if (!this.__store) {
          this.__store = new qx.data.store.Yql(value, this.__getDelegate());
          this.__store.bind("model", this.getChildControl("list"), "model");
          this.__createTimer();
          this.__timer.addListener("interval", this.__store.reload, this);
        }
      }
    },

    __createTimer: function() {
      if (!this.__timer) {
        this.__timer = new qx.event.Timer(this.getRefreshRate());
        this.bind("refreshRate", this.__timer, "interval", {
          converter: function(value) {
            return value * 1000;
          }
        });
      }
    },

    __getDelegate: function() {
      return {
        manipulateData: function(data) {
          return data.query.results.item;
        }
      }
    }
  },

  defer: function () {
    gosa.data.DashboardController.registerWidget(gosa.plugins.yql.Main, {
      displayName: qx.locale.Manager.tr("YQL"),
      defaultColspan: 3,
      theme: {
        appearance : gosa.plugins.yql.Appearance
      },
      settings: {
        mandatory: ["query"],
        types: {
          query: "String",
          refreshRate: "Number"
        }
      }
    });
  }
});