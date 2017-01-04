/*========================================================================

 This file is part of the GOsa project -  http://gosa-project.org

 Copyright:
 (C) 2010-2016 GONICUS GmbH, Germany, http://www.gonicus.de

 License:
 LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

 See the LICENSE file in the project's top-level directory for details.

 ======================================================================== */

/**
 * Dashboard widget that shows a search field and forwards to the search results if something gets entered
 */
qx.Class.define("gosa.plugins.search.Main", {
  extend : gosa.plugins.AbstractDashboardWidget,

  construct : function() {
    this.base(arguments);
    this.getChildControl("container").setLayout(new qx.ui.layout.HBox());
  },

  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    NAME: "Search"
  },

  /*
   *****************************************************************************
   PROPERTIES
   *****************************************************************************
   */
  properties : {
    appearance: {
      refine: true,
      init: "gosa-dashboard-widget-search"
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

        case "search-field":
          control = new qx.ui.form.TextField('');
          control.setPlaceholder(this.tr("Please enter your search..."));
          this.getChildControl("container").add(control, {flex: 1});
          break;

        case "search-button":
          var command = new qx.ui.command.Command("enter");
          control = new qx.ui.form.Button(this.tr("Search"), "@Ligature/search", command);
          this.getChildControl("container").add(control);
          break;
      }



      return control || this.base(arguments, id);
    },

    draw: function() {
      var field = this.getChildControl("search-field");
      var button = this.getChildControl("search-button");
      new qx.util.DeferredCall(function() {
        var searchView = gosa.view.Search.getInstance();
        button.addListener("execute", function() {
          gosa.Application.showPage("search");
          searchView.doSearch();
        }, this);
        field.addListener("changeValue", function(ev) {
          searchView.searchField.setValue(ev.getData());
        }, this);
      }, this).schedule();
    }
  },

  defer: function () {
    gosa.view.Dashboard.registerWidget(gosa.plugins.search.Main, {
      name: qx.locale.Manager.tr("Search"),
      theme: {
        appearance : gosa.plugins.search.Appearance
      },
      defaultColspan: 6
    });
  }
});