/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Container showing several tabs - all necessary for displaying forms for editing an object.
 */
qx.Class.define("gosa.ui.widgets.ObjectEdit", {

  extend: qx.ui.container.Composite,

  /**
   * @param obj {gosa.proxy.Object} The object for which this widget shows tabs with edit forms
   * @param templates {Array} List of template objects; each appears in its own tab
   */
  construct: function(obj, templates) {
    this.base(arguments);

    qx.core.Assert.assertInstance(obj, gosa.proxy.Object);
    qx.core.Assert.assertArray(templates);
    this._obj = obj;
    this._templates = templates;

    this._contexts = [];

    this.setLayout(new qx.ui.layout.VBox());
    this._initWidgets();
  },

  members : {

    _obj : null,
    _templates : null,
    _tabView : null,
    _toolMenu : null,
    _buttonPane : null,
    _contexts : null,

    _initWidgets : function() {
      this._createTabView();
      this._createTabPages();
      this._createToolmenu();
      this._createButtons();
    },

    _createTabView : function() {
      this._tabView = new gosa.ui.tabview.TabView();
      this._tabView.getChildControl("bar").setScrollStep(150);
      this.add(this._tabView, {flex : 1});
    },

    _createTabPages : function() {
      this._templates.forEach(function(template) {
        var tabPage = new qx.ui.tabview.Page();
        tabPage.setLayout(new qx.ui.layout.VBox());

        var context = new gosa.engine.Context(template, tabPage);
        this._contexts.push(context);
        this._tabView.add(context.getRootWidget());
      }, this);
    },

    _createToolmenu : function() {
      this._toolMenu = new qx.ui.menu.Menu();
      this._tabView.getChildControl("bar").setMenu(this._toolMenu);

      this._createActionButtons();
    },

    _createActionButtons : function() {
      var allActionEntries = {};
      var actionEntries, key;

      // collect action menu entries
      this._contexts.forEach(function(context) {
        actionEntries = context.getActions();
        for (var name in actionEntries) {
          if (actionEntries.hasOwnProperty(name)) {
            qx.core.Assert.assertFalse(allActionEntries.hasOwnProperty(name), "Duplicate action name: '" + name + "'");
            allActionEntries[name] = actionEntries[name];
          }
        }
      });

      // sort by name
      var sorted = [];
      for(key in allActionEntries) {
        sorted[sorted.length] = key;
      }
      sorted.sort();

      // add menu entries to widget
      sorted.forEach(function(key) {
        this._toolMenu.add(allActionEntries[key]);
      }, this);
    },

    _createButtons : function() {
      var paneLayout = new qx.ui.layout.HBox();
      paneLayout.set({
        spacing: 4,
        alignX : "right",
        alignY : "middle"
      });
      this._buttonPane = new qx.ui.container.Composite(paneLayout);
      this._buttonPane.setMarginTop(11);

      this.add(this._buttonPane);
      this._createOkButton();
      this._createCancelButton();
    },

    _createOkButton : function() {
      var button = gosa.ui.base.Buttons.getOkButton();
      button.set({
        enabled : false,
        tabIndex : 30000
      });
      button.addState("default");
      this._buttonPane.add(button);
    },

    _createCancelButton : function() {
      var button = gosa.ui.base.Buttons.getCancelButton();
      button.setTabIndex(30001);
      this._buttonPane.add(button);
    }
  },

  destruct : function() {
    this._obj = null;
    this._templates = null;
    qx.util.DisposeUtil.disposeArray("_contexts");
    this._disposeObjects("_toolMenu", "_buttonPane", "_tabView");
  }
});